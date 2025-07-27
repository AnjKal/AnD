# Use official Python image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TOKENIZERS_PARALLELISM=true

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmupdf-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies with optimized flags
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import torch; print(f'PyTorch version: {torch.__version__}')" \
    && python -c "from sentence_transformers import SentenceTransformer; \
        SentenceTransformer('BAAI/bge-small-en-v1.5', cache_folder='/app/models')"

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/pdfs /app/output /app/models

# Set the entrypoint
ENTRYPOINT ["python", "main.py", "--data-dir", "/app/data", "--output-dir", "/app/output"]

# Default command (can be overridden)
CMD []
