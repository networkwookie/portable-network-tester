#!/bin/bash
# Customize an existing Raspberry Pi OS image with Network Tester
# This mounts an existing .img file and installs the application

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Configuration
BASE_IMAGE="$1"
OUTPUT_IMAGE="${BASE_IMAGE%.img}-network-tester.img"

if [ -z "$BASE_IMAGE" ]; then
    echo "Usage: $0 <base-raspios-image.img>"
    echo ""
    echo "Example:"
    echo "  $0 2024-03-15-raspios-bookworm-arm64-lite.img"
    echo ""
    echo "This script will:"
    echo "  1. Copy the base image"
    echo "  2. Mount it"
    echo "  3. Install Network Tester"
    echo "  4. Configure auto-start"
    echo "  5. Create a bootable image"
    exit 1
fi

if [ ! -f "$BASE_IMAGE" ]; then
    echo "Error: Base image not found: $BASE_IMAGE"
    exit 1
fi

if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root (use sudo)"
    exit 1
fi

echo "=========================================="
echo "Customizing Raspberry Pi OS Image"
echo "=========================================="
echo "Base image: $BASE_IMAGE"
echo "Output: $OUTPUT_IMAGE"
echo ""

# Copy base image
echo "Copying base image..."
cp "$BASE_IMAGE" "$OUTPUT_IMAGE"

# Get partition information
echo "Analyzing image partitions..."
LOOP_DEVICE=$(losetup -f)
losetup -P "$LOOP_DEVICE" "$OUTPUT_IMAGE"

# Wait for device to be ready
sleep 2

# Find the root partition (usually partition 2)
ROOT_PARTITION="${LOOP_DEVICE}p2"
BOOT_PARTITION="${LOOP_DEVICE}p1"

if [ ! -e "$ROOT_PARTITION" ]; then
    echo "Error: Root partition not found"
    losetup -d "$LOOP_DEVICE"
    exit 1
fi

# Create mount points
MOUNT_POINT="/tmp/raspios-mount-$$"
mkdir -p "$MOUNT_POINT"

echo "Mounting root partition..."
mount "$ROOT_PARTITION" "$MOUNT_POINT"
mount "$BOOT_PARTITION" "$MOUNT_POINT/boot"

# Copy application files
echo "Installing Network Tester..."
mkdir -p "$MOUNT_POINT/opt/network-tester"

cp -r "$PROJECT_ROOT/src" "$MOUNT_POINT/opt/network-tester/"
cp -r "$PROJECT_ROOT/tests" "$MOUNT_POINT/opt/network-tester/"
cp "$PROJECT_ROOT/pyproject.toml" "$MOUNT_POINT/opt/network-tester/"
cp "$PROJECT_ROOT/README.md" "$MOUNT_POINT/opt/network-tester/"
cp "$PROJECT_ROOT/config.example.yml" "$MOUNT_POINT/opt/network-tester/config.yml"
cp -r "$PROJECT_ROOT/scripts" "$MOUNT_POINT/opt/network-tester/"

# Configure for fullscreen
sed -i 's/fullscreen: false/fullscreen: true/g' "$MOUNT_POINT/opt/network-tester/config.yml"

# Create installation script to run on first boot
cat > "$MOUNT_POINT/opt/network-tester-install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
set -e

echo "Installing Network Tester dependencies..."

# Update package list
apt-get update

# Install system dependencies
apt-get install -y \
    python3 python3-pip python3-venv \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    pkg-config libgl1-mesa-dev libgles2-mesa-dev \
    python3-setuptools libgstreamer1.0-dev \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
    gstreamer1.0-omx gstreamer1.0-alsa \
    python3-dev libmtdev-dev xclip xsel libjpeg-dev \
    tcpdump net-tools ethtool lldpd iputils-ping traceroute

# Enable LLDP
systemctl enable lldpd
systemctl start lldpd

# Create virtual environment
cd /opt/network-tester
python3 -m venv venv

# Install Python packages
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -e .

# Set proper permissions
chown -R pi:pi /opt/network-tester

# Install systemd service
cp /opt/network-tester/scripts/network-tester.service /etc/systemd/system/
sed -i 's|/home/pi/portable-network-tester|/opt/network-tester|g' /etc/systemd/system/network-tester.service
systemctl enable network-tester

# Clean up
apt-get clean
rm -rf /var/lib/apt/lists/*

# Create completion marker
touch /opt/network-tester/.installed

# Remove this script
rm /opt/network-tester-install.sh

echo "Network Tester installation complete!"
INSTALL_SCRIPT

chmod +x "$MOUNT_POINT/opt/network-tester-install.sh"

# Add to rc.local for first-boot installation
if [ -f "$MOUNT_POINT/etc/rc.local" ]; then
    # Backup original
    cp "$MOUNT_POINT/etc/rc.local" "$MOUNT_POINT/etc/rc.local.backup"
    
    # Remove exit 0
    sed -i '/^exit 0/d' "$MOUNT_POINT/etc/rc.local"
    
    # Add our installation script
    cat >> "$MOUNT_POINT/etc/rc.local" << 'RC_LOCAL'

# Network Tester first-boot installation
if [ -f /opt/network-tester-install.sh ]; then
    /opt/network-tester-install.sh >> /var/log/network-tester-install.log 2>&1
fi

exit 0
RC_LOCAL
else
    # Create rc.local if it doesn't exist
    cat > "$MOUNT_POINT/etc/rc.local" << 'RC_LOCAL'
#!/bin/bash

# Network Tester first-boot installation
if [ -f /opt/network-tester-install.sh ]; then
    /opt/network-tester-install.sh >> /var/log/network-tester-install.log 2>&1
fi

exit 0
RC_LOCAL
    chmod +x "$MOUNT_POINT/etc/rc.local"
fi

# Set hostname
echo "network-tester" > "$MOUNT_POINT/etc/hostname"
sed -i 's/127.0.1.1.*/127.0.1.1\tnetwork-tester/g' "$MOUNT_POINT/etc/hosts"

# Enable SSH
touch "$MOUNT_POINT/boot/ssh"

# Create image info
cat > "$MOUNT_POINT/opt/network-tester/IMAGE_INFO" << EOF
Network Tester Image
Base: $(basename "$BASE_IMAGE")
Customized: $(date)
Version: $(grep version "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2)

Note: Dependencies will be installed on first boot (takes 5-10 minutes)
EOF

# Sync and unmount
echo "Syncing filesystem..."
sync

echo "Unmounting..."
umount "$MOUNT_POINT/boot"
umount "$MOUNT_POINT"
rmdir "$MOUNT_POINT"

losetup -d "$LOOP_DEVICE"

echo ""
echo "=========================================="
echo "Image customization complete!"
echo "=========================================="
echo "Output image: $OUTPUT_IMAGE"
echo "Size: $(du -h "$OUTPUT_IMAGE" | cut -f1)"
echo ""
echo "To write to SD card:"
echo "  sudo dd if=$OUTPUT_IMAGE of=/dev/sdX bs=4M status=progress conv=fsync"
echo "  (Replace /dev/sdX with your SD card device)"
echo ""
echo "First boot will take 5-10 minutes to install dependencies."
echo "Check installation log: /var/log/network-tester-install.log"
echo ""
echo "Default credentials:"
echo "  Username: pi"
echo "  Password: raspberry"
echo ""
