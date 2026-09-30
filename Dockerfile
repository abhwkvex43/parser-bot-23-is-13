FROM python:3.11-slim

# Install FFmpeg
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p downloads temp data logs

# Expose health check port
EXPOSE 8000

# Environment — cloud defaults (no proxy needed outside Russia)
ENV PYTHONUNBUFFERED=1
ENV PROXY_URL=""
ENV USE_LOCAL_BOT_API=false
ENV FFMPEG_PATH=ffmpeg

# Run
CMD ["python", "main.py"]
