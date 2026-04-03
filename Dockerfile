# Use Python 3.11 slim as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for OpenCV and MediaPipe
# Note: libgl1-mesa-glx was renamed to libgl1 in Debian 13 (Trixie)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
# Install torch CPU-only first (much smaller, faster — no GPU on Railway)
RUN pip install --no-cache-dir torch==2.1.1 torchvision==0.16.1 --index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source code
COPY . .

# Expose port
EXPOSE 8000

# Start the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
