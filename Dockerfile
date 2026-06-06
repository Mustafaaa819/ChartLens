FROM python:3.12.7-slim

# Prevent Python from writing .pyc files and enable stdout/stderr flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONUTF8=1

WORKDIR /app

# Install system dependencies needed by PyMuPDF
RUN apt-get update && apt-get install -y \
    libmupdf-dev \
    libfreetype6 \
    libharfbuzz0b \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create runtime directories
RUN mkdir -p uploads reports static

# /data is the HF Spaces persistent volume — survives container rebuilds
RUN mkdir -p /data && chmod -R 777 /data

# Expose port
EXPOSE 7860

# HF Spaces runs as a non-root user — set permissions
RUN chmod -R 777 uploads reports static

# Start the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]

#Persistent storage fix verified but still isn't working 

