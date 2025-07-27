# Intelligent Document Analysis System (1b)

## Overview
This system performs semantic analysis on multiple PDF documents to extract and rank relevant sections based on a given task and persona. It uses the BAAI/bge-small-en-v1.5 model for embeddings and semantic search.

## Features
- Processes multiple PDF documents in parallel
- Extracts and chunks text with smart section detection
- Performs semantic search using BGE embeddings
- Ranks sections by relevance to the given task
- Supports both CPU and GPU processing
- Docker containerization support

## Prerequisites
- Python 3.8+
- pip (Python package manager)
- Docker (optional, for containerized deployment)

## Installation

### Local Installation
1. Clone the repository
2. Navigate to the project directory:
   ```bash
   cd 1b
   ```
3. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
4. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Installation
```bash
docker build -t document-analyzer .
```

## Project Structure
```
1b/
├── data/
│   ├── input.json       # Input configuration
│   └── pdfs/           # Directory for PDF files
├── models/             # Downloaded ML models
├── output/             # Output directory for results
├── main.py             # Main entry point
├── optimized_utils.py  # Core processing logic
├── pdf_utils.py        # PDF processing utilities
└── requirements.txt    # Python dependencies
```

## Configuration
Create an `input.json` file in the `data` directory with the following structure:

```json
{
    "challenge_info": {
        "challenge_id": "round_1b_002",
        "test_case_name": "travel_planner",
        "description": "France Travel"
    },
    "documents": [
        {
            "filename": "South of France - Cities.pdf",
            "title": "South of France - Cities"
        }
    ],
    "persona": {
        "role": "Travel Planner"
    },
    "job_to_be_done": {
        "task": "Plan a trip of 4 days for a group of 10 college friends."
    }
}
```

## Usage

### Local Execution
1. Place your PDF files in the `data/pdfs/` directory
2. Update `data/input.json` with your configuration
3. Run the analysis:
   ```bash
   python main.py --data-dir ./data --output-dir ./results --top-n 10
   ```

### Docker Execution
```bash
docker run -v $(pwd)/data:/app/data -v $(pwd)/results:/app/output document-analyzer
```

### Command Line Arguments
- `--data-dir`: Directory containing input.json and pdfs/ (default: ./data)
- `--output-dir`: Directory to save results (default: ./output)
- `--top-n`: Number of top results to return (default: 10)

## Output
Results are saved in `results/summary.json` with the following structure:

```json
{
  "challenge_info": {...},
  "metadata": {
    "input_documents": [...],
    "persona": "...",
    "job_to_be_done": "...",
    "processing_timestamp": "...",
    "model_used": "..."
  },
  "extracted_sections": [...],
  "subsection_analysis": [...]
}
```

## Performance Tips
- The system automatically uses GPU if available
- Processing is parallelized across multiple CPU cores
- Results are cached to improve performance on subsequent runs

## Troubleshooting
- Ensure all PDF files listed in `input.json` exist in the `pdfs/` directory
- Check that you have sufficient disk space for the model (≈500MB)
- For memory issues, reduce the number of parallel processes or use smaller document chunks
