#!/usr/bin/env python3
import sys
import json
import fitz  # PyMuPDF
from collections import defaultdict
from pathlib import Path

class PDFOutlineExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = Path(pdf_path)
        self.doc = fitz.open(self.pdf_path)
        self.font_sizes = set()
        self.text_blocks = []

    def extract_text_blocks(self):
        """Extract all text blocks with their font sizes and positions."""
        for page_num, page in enumerate(self.doc, start=1):
            blocks = page.get_text("dict", flags=fitz.TEXTFLAGS_TEXT)['blocks']
            for block in blocks:
                if 'lines' in block:
                    for line in block['lines']:
                        for span in line['spans']:
                            if span['text'].strip():
                                self.text_blocks.append({
                                    'text': span['text'].strip(),
                                    'size': round(span['size'], 2),
                                    'page': page_num,
                                    'bbox': span['bbox']
                                })
                                self.font_sizes.add(round(span['size'], 2))

    def determine_heading_levels(self):
        """Map font sizes to heading levels."""
        if not self.font_sizes:
            return {}
            
        # Sort font sizes in descending order
        sorted_sizes = sorted(self.font_sizes, reverse=True)
        
        # Assign heading levels based on size ranking
        heading_levels = {}
        for i, size in enumerate(sorted_sizes):
            if i == 0:
                heading_levels[size] = "H1"
            elif i == 1:
                heading_levels[size] = "H2"
            elif i == 2:
                heading_levels[size] = "H3"
            else:
                heading_levels[size] = "P"  # Paragraph
                
        return heading_levels

    def extract_outline(self):
        """Extract the document outline based on font sizes."""
        self.extract_text_blocks()
        heading_levels = self.determine_heading_levels()
        
        # Get title (first H1 on first page)
        title = next((block['text'] for block in self.text_blocks 
                     if block['page'] == 1 and 
                     heading_levels.get(block['size']) == "H1"), "")
        
        # Get outline items (H1-H3)
        outline = []
        for block in self.text_blocks:
            level = heading_levels.get(block['size'])
            if level in ["H1", "H2", "H3"]:
                outline.append({
                    "level": level,
                    "text": block['text'],
                    "page": block['page']
                })
        
        return {
            "title": title,
            "outline": outline
        }

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"Error: File '{pdf_path}' not found.")
        sys.exit(1)
    
    try:
        extractor = PDFOutlineExtractor(pdf_path)
        result = extractor.extract_outline()
        
        # Write to outline.json in the same directory as the input PDF
        output_path = Path(pdf_path).parent / "outline.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"Outline extracted successfully to: {output_path}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

    