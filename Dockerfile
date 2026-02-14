FROM python:3.9-slim

# Install system dependencies for dlib and opencv
RUN apt-get update && apt-get install -y \
    cmake \
    build-essential \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the port (Render handles this dynamically, but good for documentation)
EXPOSE 5001

CMD ["python", "app.py"]
