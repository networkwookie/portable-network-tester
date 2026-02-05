#!/bin/bash
# Setup script for Portable Network Tester on Raspberry Pi

set -e

echo "====================================="
echo "Portable Network Tester Setup"
echo "====================================="

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    pkg-config \
    libgl1-mesa-dev \
    libgles2-mesa-dev \
    python3-setuptools \
    libgstreamer1.0-dev \
    git-core \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-omx \
    gstreamer1.0-alsa \
    python3-dev \
    libmtdev-dev \
    xclip \
    xsel \
    libjpeg-dev \
    tcpdump \
    net-tools \
    ethtool \
    lldpd \
    iputils-ping \
    traceroute

# Enable and start LLDP daemon
echo "Configuring LLDP daemon..."
sudo systemctl enable lldpd
sudo systemctl start lldpd

# Create virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -e ".[dev]"

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Create logs directory
mkdir -p logs

# Create default config if it doesn't exist
if [ ! -f config.yml ]; then
    echo "Creating default configuration..."
    cp config.example.yml config.yml
fi

echo ""
echo "====================================="
echo "Setup complete!"
echo "====================================="
echo ""
echo "To run the application:"
echo "  source venv/bin/activate"
echo "  python src/main.py"
echo ""
echo "To run tests:"
echo "  source venv/bin/activate"
echo "  pytest"
echo ""
echo "To install as a service:"
echo "  sudo cp scripts/network-tester.service /etc/systemd/system/"
echo "  sudo systemctl enable network-tester"
echo "  sudo systemctl start network-tester"
echo ""
