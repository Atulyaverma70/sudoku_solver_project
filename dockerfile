# Use official Python image
FROM python:3.10-slim

# Avoid interactive prompts and speed up pip/logging
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System deps for OpenCV + Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libtesseract-dev \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy dependency spec first for better layer caching
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the source
COPY . .

# Create uploads folder with proper permissions
RUN mkdir -p /app/uploads && chmod -R 777 /app/uploads

# Expose the container's app port
EXPOSE 5000

# Gunicorn (threads + longer timeout to handle OCR)
CMD ["gunicorn", "-k", "gthread", "-w", "2", "--threads", "4", "-b", "0.0.0.0:5000", "--timeout", "180", "--graceful-timeout", "30", "app:app"]
