#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from pdf_utils import extract_sections_from_pdfs, extract_sections_from_pdf
from embedding_utils import rank_sections_by_relevance

def load_json_file(file_path: str) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading JSON file {file_path}: {str(e)}")

def save_results(results: Dict[str, Any], output_dir: str = "output") -> str:
    """Save results to a JSON file in the specified directory."""
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)
    
    output_path = output_dir / "summary.json"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    return str(output_path.resolve())

def setup_environment():
    """Ensure required directories exist."""
    Path("models").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)

def process_input_json(input_data: dict, pdf_dir: Path) -> tuple[str, str, List[Dict]]:
    """Process the input JSON and return persona, job description, and PDF sections."""
    # Extract persona and job description
    persona = input_data.get("persona", {}).get("role", "")
    job_description = input_data.get("job_to_be_done", {}).get("task", "")
    
    # Get PDF files from the documents list
    pdf_files = []
    for doc in input_data.get("documents", []):
        pdf_path = pdf_dir / doc["filename"]
        if pdf_path.exists():
            pdf_files.append(pdf_path)
        else:
            print(f"Warning: PDF file not found: {pdf_path}")
    
    if not pdf_files:
        raise ValueError("No valid PDF files found in the input directory")
    
    # Extract text from all PDFs
    all_sections = []
    for pdf_file in pdf_files:
        try:
            sections = extract_sections_from_pdf(str(pdf_file))
            all_sections.extend(sections)
        except Exception as e:
            print(f"Warning: Could not process {pdf_file.name}: {str(e)}")
    
    return persona, job_description, all_sections

def main():
    parser = argparse.ArgumentParser(
        description='Intelligent Document Analysis System using BGE-small',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory containing input.json and pdfs/ folder (default: data)'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='output',
        help='Directory to save output JSON (default: output)'
    )
    parser.add_argument(
        '--top-n',
        type=int,
        default=10,
        help='Number of top sections to include in the analysis (default: 10)'
    )
    
    args = parser.parse_args()
    
    try:
        setup_environment()
        
        # Set up paths
        data_dir = Path(args.data_dir)
        input_json = data_dir / 'input.json'
        pdf_dir = data_dir / 'pdfs'
        
        # Validate paths
        if not input_json.exists():
            raise FileNotFoundError(f"Input JSON not found: {input_json}")
            
        if not pdf_dir.exists() or not pdf_dir.is_dir():
            raise ValueError(f"PDF directory not found: {pdf_dir}")
        
        # Load input data
        input_data = load_json_file(input_json)
        
        print("Processing input data...")
        persona, job_description, sections = process_input_json(input_data, pdf_dir)
        
        if not sections:
            raise ValueError("No text sections were extracted from the PDFs")
            
        print(f"Analyzing {len(sections)} sections for relevance...")
        ranked_sections = rank_sections_by_relevance(
            sections=sections,
            job_description=job_description,
            persona=persona,
            top_n=args.top_n
        )
        
        # Get document titles from input JSON
        doc_titles = {doc["filename"]: doc["title"] for doc in input_data.get("documents", [])}
        
        # Prepare final results
        results = {
            "challenge_info": input_data.get("challenge_info", {}),
            "metadata": {
                "input_documents": [str(pdf_dir / doc["filename"]) for doc in input_data.get("documents", [])],
                "persona": persona,
                "job_to_be_done": job_description,
                "processing_timestamp": datetime.now().isoformat(),
                "model_used": "BAAI/bge-small-en-v1.5"
            },
            "extracted_sections": [
                {
                    "document": section["document"],
                    "document_title": doc_titles.get(Path(section["document"]).name, ""),
                    "page_number": section["page_number"],
                    "section_title": section.get("title", ""),
                    "importance_rank": idx + 1,
                    "relevance_score": round(section.get("relevance_score", 0), 4)
                }
                for idx, section in enumerate(ranked_sections)
            ],
            "subsection_analysis": [
                {
                    "document": section["document"],
                    "document_title": doc_titles.get(Path(section["document"]).name, ""),
                    "refined_text": section["text"][:1000],  # First 1000 chars
                    "page_number": section["page_number"],
                    "relevance_score": round(section.get("relevance_score", 0), 4)
                }
                for section in ranked_sections
            ]
        }
        
        output_path = save_results(results, args.output_dir)
        print(f"\n✅ Analysis complete! Results saved to: {output_path}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
