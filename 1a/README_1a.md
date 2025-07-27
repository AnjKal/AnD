# PDF Outline Generator (1a)

## Overview
This tool generates a structured outline from a PDF document. It analyzes the PDF's content and creates a hierarchical outline that can be used for navigation or content analysis.

## Features
- Extracts text content from PDF files
- Generates a hierarchical outline in JSON format
- Simple command-line interface
- Docker support for easy deployment

## Prerequisites
- Python 3.8+
- pip (Python package manager)
- Docker (optional, for containerized deployment)

## Installation

### Local Installation
1. Clone the repository
2. Navigate to the project directory:
   ```bash
   cd 1a
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Docker Installation
```bash
docker build -t pdf-outline-generator .
```

## Usage

### Basic Usage
```bash
python main.py --input yourfile.pdf --output outline.json
```

### Command Line Arguments
- `--input`: Path to the input PDF file (required)
- `--output`: Path to save the output JSON file (default: outline.json)
- `--min-chars`: Minimum number of characters for a section (default: 100)
- `--max-level`: Maximum heading level to include (default: 3)

### Docker Usage
```bash
docker run -v $(pwd):/app pdf-outline-generator --input /app/yourfile.pdf --output /app/outline.json
```

## Output Format
The tool generates a JSON file with the following structure:

```json
{
  "title": "Document Title",
  "sections": [
    {
      "level": 1,
      "title": "Section Title",
      "page": 1,
      "content": "Section content..."
    },
    ...
  ]
}
```

## Example
```bash
python main.py --input sample.pdf --output my_outline.json
```

## Troubleshooting
- If you encounter any issues, ensure the input PDF is not password protected
- For large PDFs, processing may take several minutes
- Make sure you have sufficient disk space for the output file

## License
[Specify License]

## Contact
[Your Contact Information]
