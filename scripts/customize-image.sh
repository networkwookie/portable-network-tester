#!/bin/bash
# Customize an existing Raspberry Pi OS image with Network Tester
# This version includes GUI support and touchscreen configuration

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
    echo "  $0 2024-03-15-raspios-bookworm-arm64.img"
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

# Find the root partition
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

# Configure boot/config.txt for 7" touchscreen
echo "Configuring touchscreen..."
cat >> "$MOUNT_POINT/boot/config.txt" << 'EOF'

# Network Tester Configuration
# 7" Touchscreen Support
dtoverlay=vc4-kms-v3d
dtoverlay=rpi-ft5406
ignore_lcd=0

# Disable rainbow splash
disable_splash=1

# HDMI settings
hdmi_force_hotplug=1
hdmi_group=2
hdmi_mode=87
hdmi_cvt=800 480 60 6 0 0 0
EOF

# Create installation script for first boot
echo "Creating first-boot installation script..."
cat > "$MOUNT_POINT/opt/network-tester-install.sh" << 'INSTALL_SCRIPT'
#!/bin/bash
set -e

echo "=========================================="
echo "Network Tester First-Boot Installation"
echo "=========================================="
echo "Started: $(date)"

# Update package list
echo "Updating package lists..."
apt-get update

# Install system dependencies
echo "Installing system dependencies..."
apt-get install -y \
    python3 python3-pip python3-venv \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    pkg-config libgl1-mesa-dev libgles2-mesa-dev \
    python3-setuptools libgstreamer1.0-dev \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly \
    gstreamer1.0-omx gstreamer1.0-alsa \
    python3-dev libmtdev-dev xclip xsel libjpeg-dev \
    tcpdump net-tools ethtool lldpd iputils-ping traceroute \
    xserver-xorg xinit lightdm \
    fonts-freefont-ttf

# Enable LLDP
echo "Enabling LLDP daemon..."
systemctl enable lldpd
systemctl start lldpd

# Create virtual environment
echo "Creating Python virtual environment..."
cd /opt/network-tester
python3 -m venv venv

# Install Python packages
echo "Installing Python dependencies..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -e .

# Set proper permissions
echo "Setting permissions..."
chown -R pi:pi /opt/network-tester

# Install systemd service
echo "Installing systemd service..."
cp /opt/network-tester/scripts/network-tester.service /etc/systemd/system/
sed -i 's|/home/pi/portable-network-tester|/opt/network-tester|g' /etc/systemd/system/network-tester.service
systemctl daemon-reload
systemctl enable network-tester

# Configure auto-login for GUI
echo "Configuring auto-login..."
mkdir -p /etc/lightdm/lightdm.conf.d
cat > /etc/lightdm/lightdm.conf.d/50-network-tester.conf << 'LIGHTDM'
[Seat:*]
autologin-user=pi
autologin-user-timeout=0
user-session=LXDE
LIGHTDM

# Ensure pi user password is set
echo "Setting pi user password..."
echo "pi:raspberry" | chpasswd

# Clean up
echo "Cleaning up..."
apt-get clean
rm -rf /var/lib/apt/lists/*

# Create completion marker
touch /opt/network-tester/.installed

# Create info file
cat > /opt/network-tester/IMAGE_INFO << 'INFOEOF'
Network Tester Image
Installation completed: $(date)
INFOEOF

echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo "The Network Tester will start automatically."
echo "Default credentials: pi / raspberry"

# Remove this script
rm /opt/network-tester-install.sh

# Reboot to start the application
echo "Rebooting in 10 seconds..."
sleep 10
reboot
INSTALL_SCRIPT

chmod +x "$MOUNT_POINT/opt/network-tester-install.sh"

# Configure rc.local for first-boot installation
echo "Configuring first-boot trigger..."
if [ -f "$MOUNT_POINT/etc/rc.local" ]; then
    cp "$MOUNT_POINT/etc/rc.local" "$MOUNT_POINT/etc/rc.local.backup"
    sed -i '/^exit 0/d' "$MOUNT_POINT/etc/rc.local"
else
    echo "#!/bin/bash" > "$MOUNT_POINT/etc/rc.local"
fi

cat >> "$MOUNT_POINT/etc/rc.local" << 'RC_LOCAL'

# Network Tester first-boot installation
if [ -f /opt/network-tester-install.sh ]; then
    /opt/network-tester-install.sh >> /var/log/network-tester-install.log 2>&1
fi

exit 0
RC_LOCAL
chmod +x "$MOUNT_POINT/etc/rc.local"

# Set hostname
echo "Configuring hostname..."
echo "network-tester" > "$MOUNT_POINT/etc/hostname"
sed -i 's/127.0.1.1.*/127.0.1.1\tnetwork-tester/g' "$MOUNT_POINT/etc/hosts"

# Enable SSH
echo "Enabling SSH..."
touch "$MOUNT_POINT/boot/ssh"

# Configure SSH to allow password authentication
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' "$MOUNT_POINT/etc/ssh/sshd_config"
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' "$MOUNT_POINT/etc/ssh/sshd_config"

# Skip initial setup wizard
echo "Disabling first-run wizard..."
rm -f "$MOUNT_POINT/etc/xdg/autostart/piwiz.desktop"
touch "$MOUNT_POINT/etc/xdg/autostart/.skip-wizard"

# Also disable wizard in alternative location
if [ -f "$MOUNT_POINT/usr/share/applications/piwiz.desktop" ]; then
    sudo mv "$MOUNT_POINT/usr/share/applications/piwiz.desktop" "$MOUNT_POINT/usr/share/applications/piwiz.desktop.disabled"
fi

# Configure SSH to allow password authentication
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/g' "$MOUNT_POINT/etc/ssh/sshd_config"
sed -i 's/PasswordAuthentication no/PasswordAuthentication yes/g' "$MOUNT_POINT/etc/ssh/sshd_config"

# Ensure pi user exists with correct password
echo "Ensuring pi user exists..."
if ! grep -q "^pi:" "$MOUNT_POINT/etc/passwd"; then
    echo "Creating pi user..."
    chroot "$MOUNT_POINT" useradd -m -s /bin/bash -G sudo,video,audio,plugdev,netdev pi
fi

# Set password (this will be reset on first boot, but provides fallback)
chroot "$MOUNT_POINT" sh -c 'echo "pi:raspberry" | chpasswd'

# Create image info at root
cat > "$MOUNT_POINT/opt/network-tester/IMAGE_INFO" << EOF
Network Tester Image
Base: $(basename "$BASE_IMAGE")
Customized: $(date)
Version: $(grep version "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2)

Configuration:
- GUI: Enabled (LXDE)
- Touchscreen: Configured (7" official display)
- SSH: Enabled
- Auto-login: Enabled (user: pi)
- Default Password: raspberry

First Boot:
- Installation takes 10-15 minutes
- System will reboot automatically when complete
- Application starts automatically after reboot

Logs:
- Installation: /var/log/network-tester-install.log
- Application: /opt/network-tester/logs/network_tester.log
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
echo "Image features:"
echo "  ✓ GUI enabled (LXDE desktop)"
echo "  ✓ 7\" touchscreen configured"
echo "  ✓ Auto-login enabled"
echo "  ✓ SSH enabled"
echo "  ✓ Network Tester pre-installed"
echo ""
echo "To write to SD card:"
echo "  sudo dd if=$OUTPUT_IMAGE of=/dev/sdX bs=4M status=progress conv=fsync"
echo ""
echo "First boot:"
echo "  - Takes 10-15 minutes to install dependencies"
echo "  - System will reboot automatically"
echo "  - Application starts on second boot"
echo ""
echo "Default credentials:"
echo "  Username: pi"
echo "  Password: raspberry"
echo ""
