import fitz  # PyMuPDF
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Define common section headers that might appear in travel documents
TRAVEL_SECTION_HEADERS = [
    'itinerary', 'accommodation', 'transportation', 'activities',
    'dining', 'sightseeing', 'day 1', 'day 2', 'day 3', 'day 4',
    'introduction', 'overview', 'tips', 'recommendations', 'budget'
]

def is_section_header(text: str) -> bool:
    """Check if the text appears to be a section header."""
    # Check for all caps or title case with common section patterns
    if not text or len(text) > 100:  # Too long to be a header
        return False
    
    text_lower = text.lower().strip()
    
    # Check for common section headers
    if any(header in text_lower for header in TRAVEL_SECTION_HEADERS):
        return True
    
    # Check for numbered sections (e.g., "1. Introduction")
    if re.match(r'^\s*\d+[.)]\s+[A-Z]', text):
        return True
    
    # Check for all-caps or title-cased text that's not too long
    words = text.split()
    if len(words) < 6 and (text.isupper() or text.istitle()):
        return True
    
    return False

def extract_sections_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract sections from a single PDF file with better handling of travel documents.
    Returns a list of sections with their text, page numbers, and metadata.
    """
    doc = fitz.open(pdf_path)
    sections = []
    current_section = None
    
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)['blocks']
        
        # Group text by font size to identify headings
        text_blocks = []
        for block in blocks:
            if 'lines' in block:
                for line in block['lines']:
                    for span in line['spans']:
                        text = span['text'].strip()
                        if text:
                            text_blocks.append({
                                'text': text,
                                'size': span['size'],
                                'font': span['font'],
                                'bold': 'bold' in span['font'].lower(),
                                'page': page_num + 1,
                                'bbox': span['bbox']
                            })
        
        # Process text blocks to identify sections
        for i, block in enumerate(text_blocks):
            text = block['text']
            
            # Check if this looks like a section header
            if is_section_header(text):
                # If we have a current section, save it before starting a new one
                if current_section and current_section['text'].strip():
                    sections.append(current_section)
                
                # Start a new section
                current_section = {
                    'document': Path(pdf_path).name,
                    'page_number': block['page'],
                    'title': text,
                    'text': '',
                    'font_size': block['size'],
                    'is_bold': block['bold'],
                    'type': 'section_header'
                }
            else:
                # Add to current section or create a new one if none exists
                if current_section is None:
                    current_section = {
                        'document': Path(pdf_path).name,
                        'page_number': block['page'],
                        'title': f"Content from page {block['page']}",
                        'text': '',
                        'font_size': block['size'],
                        'is_bold': False,
                        'type': 'content'
                    }
                
                # Add text to current section with proper spacing
                if current_section['text'] and not current_section['text'].endswith(' '):
                    current_section['text'] += ' '
                current_section['text'] += text
        
        # Add a section break at page boundaries
        if current_section and current_section['text'].strip():
            current_section['text'] += '\n\n'
    # Add the last section if it exists
    if current_section and current_section['text'].strip():
        sections.append(current_section)
    
    # If no sections were found (e.g., scanned PDF), fall back to page-based sections
    if not sections:
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text("text")
            if text.strip():
                sections.append({
                    'document': Path(pdf_path).name,
                    'page_number': page_num + 1,
                    'title': f"Page {page_num + 1}",
                    'text': text,
                    'font_size': 0,
                    'is_bold': False,
                    'type': 'page_content'
                })
    
    return sections

def extract_sections_from_pdfs(pdf_dir: str) -> List[Dict[str, Any]]:
    """Extract sections from all PDFs in a directory."""
    pdf_dir = Path(pdf_dir)
    if not pdf_dir.exists() or not pdf_dir.is_dir():
        raise ValueError(f"Directory not found: {pdf_dir}")
    
    all_sections = []
    for pdf_file in pdf_dir.glob("*.pdf"):
        try:
            sections = extract_sections_from_pdf(str(pdf_file))
            all_sections.extend(sections)
        except Exception as e:
            print(f"Warning: Could not process {pdf_file}: {str(e)}")
    
    return all_sections
