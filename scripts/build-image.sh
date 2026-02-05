#!/bin/bash
# Build custom Raspberry Pi OS image using pi-gen
# This creates a bootable .img file with the Network Tester pre-installed

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BUILD_DIR="${PROJECT_ROOT}/build/pi-gen"
PI_GEN_REPO="https://github.com/RPi-Distro/pi-gen.git"

echo "=========================================="
echo "Network Tester Image Builder (pi-gen)"
echo "=========================================="

# Check for required tools
for tool in git qemu-user-static debootstrap; do
    if ! command -v $tool &> /dev/null; then
        echo "Error: $tool is required but not installed."
        echo "On Debian/Ubuntu: sudo apt-get install git qemu-user-static debootstrap"
        exit 1
    fi
done

# Create build directory
echo "Setting up build environment..."
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Clone pi-gen if not already present
if [ ! -d "pi-gen" ]; then
    echo "Cloning pi-gen repository..."
    git clone "$PI_GEN_REPO"
fi

cd pi-gen

# Create config
echo "Creating pi-gen configuration..."
cat > config << EOF
IMG_NAME=network-tester
RELEASE=bookworm
DEPLOY_COMPRESSION=xz
LOCALE_DEFAULT=en_US.UTF-8
TARGET_HOSTNAME=network-tester
KEYBOARD_KEYMAP=us
KEYBOARD_LAYOUT="English (US)"
TIMEZONE_DEFAULT=UTC
FIRST_USER_NAME=pi
FIRST_USER_PASS=raspberry
ENABLE_SSH=1
STAGE_LIST="stage0 stage1 stage2"
EOF

# Create custom stage for Network Tester
echo "Creating custom stage..."
CUSTOM_STAGE="stage3-network-tester"
mkdir -p "$CUSTOM_STAGE"

# Create prerun script
cat > "$CUSTOM_STAGE/prerun.sh" << 'PRERUN'
#!/bin/bash -e
echo "Setting up Network Tester stage..."
PRERUN
chmod +x "$CUSTOM_STAGE/prerun.sh"

# Create main installation script
mkdir -p "$CUSTOM_STAGE/00-network-tester"
cat > "$CUSTOM_STAGE/00-network-tester/00-run.sh" << 'RUNSCRIPT'
#!/bin/bash -e

on_chroot << EOF
# Update package list
apt-get update

# Install system dependencies
apt-get install -y \
    python3 python3-pip python3-venv \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    pkg-config libgl1-mesa-dev libgles2-mesa-dev \
    python3-setuptools libgstreamer1.0-dev git-core \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
    gstreamer1.0-omx gstreamer1.0-alsa \
    python3-dev libmtdev-dev xclip xsel libjpeg-dev \
    tcpdump net-tools ethtool lldpd iputils-ping traceroute

# Enable LLDP
systemctl enable lldpd

# Create application directory
mkdir -p /opt/network-tester

# Copy application files (will be added below)
cd /opt/network-tester

# Create virtual environment
python3 -m venv venv

# Install application
./venv/bin/pip install --upgrade pip

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*
EOF
RUNSCRIPT
chmod +x "$CUSTOM_STAGE/00-network-tester/00-run.sh"

# Copy application files to stage
mkdir -p "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester"
cp -r "${PROJECT_ROOT}/src" "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/"
cp -r "${PROJECT_ROOT}/tests" "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/"
cp "${PROJECT_ROOT}/pyproject.toml" "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/"
cp "${PROJECT_ROOT}/README.md" "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/"
cp "${PROJECT_ROOT}/config.example.yml" "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/config.yml"
cp -r "${PROJECT_ROOT}/scripts" "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/"

# Set fullscreen in config
sed -i 's/fullscreen: false/fullscreen: true/g' "$CUSTOM_STAGE/00-network-tester/files/opt/network-tester/config.yml"

# Create systemd service installation script
cat > "$CUSTOM_STAGE/00-network-tester/01-run.sh" << 'RUNSCRIPT2'
#!/bin/bash -e

on_chroot << EOF
# Install Python dependencies
cd /opt/network-tester
./venv/bin/pip install -e .

# Install systemd service
cp /opt/network-tester/scripts/network-tester.service /etc/systemd/system/
sed -i 's|/home/pi/portable-network-tester|/opt/network-tester|g' /etc/systemd/system/network-tester.service
systemctl enable network-tester

# Set proper permissions
chown -R pi:pi /opt/network-tester

# Create image info
cat > /opt/network-tester/IMAGE_INFO << INFOEOF
Network Tester Image
Built: $(date)
INFOEOF
EOF
RUNSCRIPT2
chmod +x "$CUSTOM_STAGE/00-network-tester/01-run.sh"

# Add custom stage to STAGE_LIST
echo "STAGE_LIST=\"stage0 stage1 stage2 $CUSTOM_STAGE\"" >> config

echo "Starting image build (this will take 30-60 minutes)..."
echo "Building in: $(pwd)"

# Build the image
sudo ./build.sh

# Copy the resulting image
if [ -f deploy/*.img* ]; then
    OUTPUT_DIR="${PROJECT_ROOT}/build/images"
    mkdir -p "$OUTPUT_DIR"
    cp deploy/*.img* "$OUTPUT_DIR/"
    echo ""
    echo "=========================================="
    echo "Build Complete!"
    echo "=========================================="
    echo "Image location: $OUTPUT_DIR"
    ls -lh "$OUTPUT_DIR"
    echo ""
    echo "To write to SD card:"
    echo "  sudo dd if=$OUTPUT_DIR/*.img of=/dev/sdX bs=4M status=progress"
    echo "  (Replace /dev/sdX with your SD card device)"
else
    echo "Error: Image file not found in deploy directory"
    exit 1
fi
