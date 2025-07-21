# PDF Outline Extractor

A command-line tool that extracts a structured outline from PDF documents using PyMuPDF (fitz). The tool identifies headings (H1, H2, H3) based on font size and generates a JSON outline.

## Features

- Extracts document title (largest font on first page)
- Identifies heading levels (H1, H2, H3) based on font size
- Outputs a clean JSON structure with page numbers
- Runs in a Docker container for easy deployment
- Works offline with no external dependencies

## How It Works

1. **Text Extraction**: The script uses PyMuPDF to extract text blocks along with their font sizes and positions.
2. **Heading Detection**: Font sizes are analyzed to determine heading levels:
   - Largest font size → H1
   - Second largest → H2
   - Third largest → H3
3. **Title Extraction**: The first H1 heading on the first page is considered the document title.
4. **Output**: Generates a JSON file with the title and outline structure.

## Requirements

- Docker
- A PDF file to process

## Installation

1. Clone this repository or copy the files to your working directory.
2. Build the Docker image:
   ```bash
   docker build -t pdf-outline-extractor .
   ```

## Usage

### Basic Usage

```bash
# Navigate to your PDF directory
cd /path/to/your/pdf/folder

# Run the container (replace 'yourfile.pdf' with your PDF filename)
docker run -v ${PWD}:/app/pdf pdf-outline-extractor /app/pdf/yourfile.pdf
```

### Windows Users

```powershell
# Navigate to your PDF directory
cd "C:\path\to\your\pdf\folder"

# Run the container
docker run -v ${PWD}:/app/pdf pdf-outline-extractor /app/pdf/yourfile.pdf
```

### Output

The tool creates an `outline.json` file in the same directory as your input PDF. The JSON structure includes:

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Chapter 1",
      "page": 1
    },
    {
      "level": "H2",
      "text": "Section 1.1",
      "page": 2
    }
  ]
}
```

## Project Structure

```
.
├── Dockerfile          # Docker configuration
├── main.py            # Main Python script
├── README.md          # This file
└── requirements.txt   # Python dependencies
```

## Troubleshooting

1. **Docker not found**:
   - Ensure Docker Desktop is installed and running
   - Verify Docker is in your system PATH

2. **File not found**:
   - Check that the PDF file exists in the specified path
   - Use absolute paths if relative paths don't work

3. **Permission issues**:
   - On Linux/macOS, you might need to use `sudo` or add your user to the docker group

## License

This project is open source and available under the [MIT License](LICENSE).
