FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    pkg-config \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    git \
    tcpdump \
    net-tools \
    ethtool \
    lldpd \
    iputils-ping \
    traceroute \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml .
COPY README.md .
COPY src/ src/
COPY tests/ tests/

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Create logs directory
RUN mkdir -p logs

# Run tests by default
CMD ["pytest", "-v"]
