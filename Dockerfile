# Use Python slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for various document processing
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    pkg-config \
    tesseract-ocr \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY ./app .

# Create directory for ChromaDB persistence
RUN mkdir -p /tmp/chroma_db

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
