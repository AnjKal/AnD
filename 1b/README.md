# Intelligent Document Analysis System

A command-line tool that analyzes PDF documents using the BAAI/bge-small-en-v1.5 model to find and rank relevant sections based on a specified persona and job description.

## ✨ Features

- 📄 Extracts text and metadata from PDFs using PyMuPDF
- 🤖 Uses BAAI/bge-small-en-v1.5 for high-quality semantic search
- 🎯 Ranks document sections by relevance to the job description
- 📊 Generates structured JSON output with relevance scores
- 🔒 Works entirely offline with pre-downloaded models
- ⚡ Optimized for CPU with models under 1GB

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Download the BGE-small model** (only needed once):
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5').save('./models/bge-small-en-v1.5')"
   ```

3. **Prepare your input files**:
   ```bash
   # Create input directory structure
   mkdir -p data/pdfs
   
   # Add your PDFs to data/pdfs/
   # Create persona.txt and job.txt in the data/ directory
   ```

4. **Run the analysis**:
   ```bash
   python main.py data/pdfs/ --persona data/persona.txt --job data/job.txt
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
# or
source venv/bin/activate  # On macOS/Linux
```

3. Install the required dependencies:

```bash
pip install -r requirements.txt
```

4. Download the BGE-small model (first time only):

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-small-en-v1.5').save('./models/bge-small-en-v1.5')"
```

## Usage

### Input Format

Create a JSON file (e.g., `input.json`) with the following structure:

```json
{
  "challenge_info": {
    "challenge_id": "example_001",
    "test_case_name": "travel_planner",
    "description": "France Travel"
  },
  "documents": [
    {
      "filename": "South of France - Cities.pdf",
      "title": "South of France - Cities"
    },
    {
      "filename": "South of France - Cuisine.pdf",
      "title": "South of France - Cuisine"
    }
  ],
  "persona": {
    "role": "Travel Planner"
  },
  "job_to_be_done": {
    "task": "Plan a 4-day trip for a group of 10 college friends..."
  }
}
```

### Folder Structure

Organize your files like this:
```
data/
├── input.json       # Your input configuration
└── pdfs/           # Put all PDFs here
    ├── South of France - Cities.pdf
    ├── South of France - Cuisine.pdf
    └── ...
```

### Running the Analysis

```bash
python main.py --data-dir ./data --output-dir ./results --top-n 10
```

### Arguments

- `--data-dir`: Directory containing `input.json` and `pdfs/` folder (default: 'data')
- `--output-dir`: Output directory (default: 'output')
- `--top-n`: Number of top sections to include (default: 10)

## Example

1. Create a `data` folder in your project
2. Inside it, create a `pdfs` folder and put all your PDFs there
3. Place your `input.json` in the `data` folder (use `sample_input.json` as a template)
4. Run the analysis:

```bash
python main.py --data-dir ./data --output-dir ./results
```

## Output Format

The system generates a `summary.json` file in the output directory with the following structure:

```json
{
  "challenge_info": {
    "challenge_id": "round_1b_002",
    "test_case_name": "travel_planner",
    "description": "France Travel"
  },
  "metadata": {
    "input_documents": [
      "documents/South of France - Cities.pdf",
      "documents/South of France - Cuisine.pdf"
    ],
    "persona": "Travel Planner",
    "job_to_be_done": "Plan a trip of 4 days for a group of 10 college friends...",
    "processing_timestamp": "2025-01-01T12:00:00.000000",
    "model_used": "BAAI/bge-small-en-v1.5"
  },
  "extracted_sections": [
    {
      "document": "South of France - Cities.pdf",
      "document_title": "South of France - Cities",
      "page_number": 3,
      "section_title": "Nice: The Capital of the French Riviera",
      "importance_rank": 1,
      "relevance_score": 0.9245
    }
  ],
  "subsection_analysis": [
    {
      "document": "South of France - Cities.pdf",
      "document_title": "South of France - Cities",
      "refined_text": "Nice offers beautiful beaches along the Promenade des Anglais...",
      "page_number": 3,
      "relevance_score": 0.9245
    }
  ]
}
```

## Project Structure

```
.
├── main.py                 # Main CLI interface
├── pdf_utils.py           # PDF text extraction utilities
├── embedding_utils.py     # Semantic search and ranking with travel optimizations
├── requirements.txt       # Python dependencies
├── sample_input.json      # Example input file
└── README.md             # This file
```

## Requirements

- Python 3.8+
- PyMuPDF
- sentence-transformers
- torch
- transformers
- safetensors
