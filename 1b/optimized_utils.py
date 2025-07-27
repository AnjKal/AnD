import os
import time
import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
from multiprocessing import Pool, cpu_count
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer, util
import torch

def load_json_file(file_path: str) -> dict:
    """Load and parse a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Error loading JSON file {file_path}: {str(e)}")

def extract_text_from_pdf(pdf_path: str) -> List[Tuple[int, str]]:
    """
    Extracts text per page from a PDF using PyMuPDF.
    Returns a list of (page_number, text).
    """
    text_per_page = []
    try:
        doc = fitz.open(pdf_path)
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                text_per_page.append((i + 1, text))
    except Exception as e:
        print(f"Warning: Could not process {pdf_path}: {str(e)}")
    return text_per_page

def sliding_window_chunks(text: str, window: int = 500, stride: int = 400) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    return [" ".join(words[i:i + window]) for i in range(0, len(words), stride)]

def _process_single_pdf_global(pdf_path: str) -> List[Tuple[str, int, str]]:
    """Global function to process a single PDF file for multiprocessing."""
    doc_chunks = []
    filename = os.path.basename(pdf_path)
    pages = extract_text_from_pdf(pdf_path)
    for page_num, text in pages:
        for chunk in sliding_window_chunks(text):
            if 50 < len(chunk.split()) < 800:  # Filter extremes
                doc_chunks.append((filename, page_num, chunk))
    return doc_chunks

class DocumentProcessor:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model = SentenceTransformer(model_name)
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = self.model.to(self.device)
        
    def preprocess_pdfs(self, pdf_paths: List[str]) -> List[Tuple[str, int, str]]:
        """Process multiple PDFs in parallel using global function."""
        if not pdf_paths:
            return []
            
        # Use all available CPUs, but limit to 4 to avoid memory issues
        num_processes = min(4, len(pdf_paths), os.cpu_count() or 1)
        
        # Process in chunks to avoid memory issues
        chunk_size = min(4, len(pdf_paths))
        all_chunks = []
        
        for i in range(0, len(pdf_paths), chunk_size):
            chunk_paths = pdf_paths[i:i + chunk_size]
            with Pool(processes=num_processes) as pool:
                results = pool.map(_process_single_pdf_global, chunk_paths)
                all_chunks.extend([item for sublist in results for item in sublist])
        
        return all_chunks

    def rank_chunks(
        self, 
        chunks: List[Tuple[str, int, str]], 
        persona: str, 
        job: str,
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Rank chunks by semantic similarity to persona+job."""
        if not chunks:
            return []
            
        context_query = f"{persona}. {job}"
        texts = [chunk[2] for chunk in chunks]
        
        # Batch encode all chunks
        chunk_embeddings = self.model.encode(
            texts, 
            convert_to_tensor=True, 
            normalize_embeddings=True,
            show_progress_bar=True,
            batch_size=32
        )
        
        # Encode query
        query_embedding = self.model.encode(
            [context_query], 
            convert_to_tensor=True, 
            normalize_embeddings=True
        )
        
        # Calculate similarities
        scores = util.cos_sim(query_embedding, chunk_embeddings)[0].tolist()
        
        # Combine results with scores
        ranked = [
            {
                "document": doc,
                "document_title": os.path.splitext(doc)[0],
                "page_number": page,
                "section_title": f"Page {page}",
                "text": chunk,
                "relevance_score": round(score, 4)
            }
            for (doc, page, chunk), score in zip(chunks, scores)
        ]
        
        # Sort by score in descending order
        ranked.sort(key=lambda x: x["relevance_score"], reverse=True)
        return ranked[:top_n]

def process_documents(
    data_dir: str = "data",
    output_dir: str = "output",
    top_n: int = 10
) -> Dict[str, Any]:
    """Main processing function with timing."""
    start_time = time.time()
    
    # Load input data
    input_data = load_json_file(Path(data_dir) / "input.json")
    
    # Get PDF paths
    pdf_dir = Path(data_dir) / "pdfs"
    pdf_paths = [str(pdf_dir / doc["filename"]) for doc in input_data.get("documents", [])]
    
    # Initialize processor
    processor = DocumentProcessor()
    
    # Process PDFs
    print("⏳ Extracting and chunking PDFs...")
    chunks = processor.preprocess_pdfs(pdf_paths)
    print(f"✅ Extracted {len(chunks)} chunks from {len(pdf_paths)} PDFs")
    
    # Rank chunks
    print("⏳ Ranking relevant chunks...")
    persona = input_data.get("persona", {}).get("role", "")
    job = input_data.get("job_to_be_done", {}).get("task", "")
    
    ranked_sections = processor.rank_chunks(chunks, persona, job, top_n=top_n)
    
    # Prepare output
    output = {
        "challenge_info": input_data.get("challenge_info", {}),
        "metadata": {
            "input_documents": [os.path.basename(p) for p in pdf_paths],
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "model_used": "BAAI/bge-small-en-v1.5",
            "processing_time_seconds": round(time.time() - start_time, 2)
        },
        "extracted_sections": [
            {
                "document": section["document"],
                "document_title": section["document_title"],
                "page_number": section["page_number"],
                "section_title": section["section_title"],
                "importance_rank": i + 1,
                "relevance_score": section["relevance_score"]
            }
            for i, section in enumerate(ranked_sections)
        ],
        "subsection_analysis": [
            {
                "document": section["document"],
                "document_title": section["document_title"],
                "refined_text": section["text"][:1000],  # First 1000 chars
                "page_number": section["page_number"],
                "relevance_score": section["relevance_score"]
            }
            for section in ranked_sections
        ]
    }
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_path = Path(output_dir) / "summary.json"
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Analysis complete! Results saved to {output_path}")
    print(f"⏱️  Total processing time: {output['metadata']['processing_time_seconds']:.2f} seconds")
    
    return output
