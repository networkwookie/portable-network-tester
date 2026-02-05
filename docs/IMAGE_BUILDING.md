# Building Raspberry Pi Images

This project provides multiple methods to create bootable Raspberry Pi OS images with the Network Tester pre-installed.

## Methods

### Method 1: Customize Existing Image (Recommended)
**Fastest and most reliable method**

This takes an existing Raspberry Pi OS image and adds the Network Tester application.

#### Prerequisites
- Linux system (or WSL2 on Windows)
- Root/sudo access
- Base Raspberry Pi OS image

#### Steps

1. **Download Base Image**
   ```bash
   wget https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64-lite.img.xz
   xz -d 2024-03-15-raspios-bookworm-arm64-lite.img.xz
   ```

2. **Customize Image**
   ```bash
   sudo ./scripts/customize-image.sh 2024-03-15-raspios-bookworm-arm64-lite.img
   ```

3. **Output**
   - Creates: `2024-03-15-raspios-bookworm-arm64-lite-network-tester.img`
   - Ready to write to SD card

#### What This Does
- Copies base image
- Mounts partitions
- Installs Network Tester files
- Configures auto-start
- Sets up first-boot installation script
- Creates bootable image

**Time:** ~5-10 minutes

---

### Method 2: Build from Scratch with pi-gen
**Full custom build using official tools**

Creates a complete Raspberry Pi OS from scratch with Network Tester integrated.

#### Prerequisites
- Debian/Ubuntu Linux (or similar)
- 20GB free disk space
- Fast internet connection

#### Steps

1. **Run Build Script**
   ```bash
   ./scripts/build-image.sh
   ```

2. **Wait**
   - Build takes 30-60 minutes
   - Downloads and compiles packages
   - Creates custom stage
   - Builds complete image

3. **Output**
   - Location: `build/images/`
   - Compressed with xz

#### What This Does
- Clones pi-gen repository
- Creates custom stage3-network-tester
- Installs all dependencies
- Configures system
- Builds bootable image

**Time:** 30-60 minutes

---

### Method 3: GitHub Actions (Automated)
**CI/CD pipeline builds images automatically**

Triggered by Git tags or manual workflow dispatch.

#### Automatic Build on Release

1. **Create Release Tag**
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0"
   git push origin v0.1.0
   ```

2. **Wait for Build**
   - GitHub Actions builds image
   - Creates release with artifacts
   - Uploads compressed image

3. **Download**
   - Go to Releases page
   - Download `.img.zip` file

#### Manual Trigger

1. Go to Actions tab in GitHub
2. Select "Build Raspberry Pi Images"
3. Click "Run workflow"
4. Choose release type
5. Wait for completion
6. Download from Artifacts

**Time:** 15-20 minutes (GitHub runners)

---

### Method 4: Packer (Advanced)
**Infrastructure-as-code approach**

Uses HashiCorp Packer for reproducible builds.

#### Prerequisites
```bash
# Install Packer
wget https://releases.hashicorp.com/packer/1.9.4/packer_1.9.4_linux_amd64.zip
unzip packer_1.9.4_linux_amd64.zip
sudo mv packer /usr/local/bin/

# Install Packer ARM plugin
packer plugins install github.com/solo-io/arm-image
```

#### Steps

1. **Build Image**
   ```bash
   cd packer
   packer build raspios.pkr.hcl
   ```

2. **Output**
   - Creates: `network-tester-raspios.img`

**Time:** 20-30 minutes

---

## Writing Image to SD Card

### Linux/Mac

```bash
# Find SD card device
lsblk

# Write image (replace /dev/sdX with your device)
sudo dd if=network-tester-*.img of=/dev/sdX bs=4M status=progress conv=fsync

# Sync
sync
```

### Windows

#### Option 1: Raspberry Pi Imager
1. Download [Raspberry Pi Imager](https://www.raspberrypi.org/software/)
2. Click "Choose OS" → "Use custom"
3. Select downloaded `.img` file
4. Select SD card
5. Click "Write"

#### Option 2: balenaEtcher
1. Download [balenaEtcher](https://www.balena.io/etcher/)
2. Click "Flash from file"
3. Select `.img` file
4. Select SD card
5. Click "Flash"

---

## Image Specifications

### Size
- Compressed: ~900MB - 1.2GB (zip/xz)
- Uncompressed: ~3.5GB - 4GB
- SD Card minimum: 8GB (16GB recommended)

### What's Included
- Raspberry Pi OS Lite (64-bit, Bookworm)
- Python 3.11+
- Network Tester application
- All system dependencies
- LLDP daemon (lldpd)
- Network tools (tcpdump, ethtool, etc.)
- Auto-start configuration

### Configuration
- Hostname: `network-tester`
- User: `pi` / Password: `raspberry`
- SSH: Enabled
- Application: Auto-starts on boot
- Display: Fullscreen mode enabled
- LLDP: Enabled and running

---

## First Boot

### Timeline
1. **Boot starts** (0:00)
2. **System initialization** (0:00 - 0:30)
3. **First-boot script runs** (0:30 - 5:00)
   - Installs Python packages
   - Configures services
   - Sets up environment
4. **Application starts** (5:00)

### What to Expect
- First boot takes 5-10 minutes
- Installation happens automatically
- LED activity indicates progress
- Screen may show login prompt initially
- Application will start when ready

### Monitoring First Boot

#### Via Serial Console
```bash
# Connect via UART/USB serial adapter
screen /dev/ttyUSB0 115200
```

#### Via SSH
```bash
# Wait for network, then:
ssh pi@network-tester.local

# Check installation log
tail -f /var/log/network-tester-install.log

# Check service status
sudo systemctl status network-tester
```

---

## Troubleshooting

### Image Won't Boot
- **Verify checksum**: Compare with `.sha256` file
- **Try re-writing**: Use `dd` with `conv=fsync`
- **Check SD card**: Use `fsck` or try different card
- **Verify compatibility**: Pi 4 Model B required

### Installation Doesn't Complete
- **Check logs**: `/var/log/network-tester-install.log`
- **Check disk space**: `df -h`
- **Manual install**: `sudo /opt/network-tester-install.sh`

### Application Won't Start
- **Check service**: `sudo systemctl status network-tester`
- **View logs**: `/opt/network-tester/logs/network_tester.log`
- **Manual start**: `cd /opt/network-tester && ./venv/bin/python src/main.py`

### No Network Connection
- **Check cable**: Ensure Ethernet connected
- **Check interface**: `ip link show`
- **Check DHCP**: `ip addr show`

---

## Advanced Customization

### Modifying the Image

1. **Mount existing image**
   ```bash
   sudo losetup -fP network-tester.img
   sudo mount /dev/loop0p2 /mnt
   sudo mount /dev/loop0p1 /mnt/boot
   ```

2. **Make changes**
   ```bash
   # Edit files in /mnt/
   sudo nano /mnt/opt/network-tester/config.yml
   ```

3. **Unmount**
   ```bash
   sudo umount /mnt/boot
   sudo umount /mnt
   sudo losetup -d /dev/loop0
   ```

### Pre-configuring WiFi

Edit `wpa_supplicant.conf` in boot partition:
```bash
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="YourNetworkName"
    psk="YourPassword"
}
```

### Changing Default Password

```bash
# On running Pi
sudo passwd pi

# Or in image before writing
sudo chroot /mnt
echo "pi:newpassword" | chpasswd
```

---

## CI/CD Integration

### Automated Release Process

1. **Commit changes**
   ```bash
   git add .
   git commit -m "Release v1.0.0"
   ```

2. **Create tag**
   ```bash
   git tag -a v1.0.0 -m "Version 1.0.0"
   ```

3. **Push**
   ```bash
   git push origin main
   git push origin v1.0.0
   ```

4. **GitHub Actions automatically:**
   - Builds image
   - Compresses
   - Calculates checksums
   - Creates GitHub Release
   - Uploads artifacts

### Workflow Triggers
- **Tag push**: `v*` pattern (e.g., v1.0.0)
- **Manual**: Workflow dispatch in Actions tab
- **Schedule**: (optional) Weekly builds

---

## Distribution

### GitHub Releases
- Automatically created on version tags
- Includes compressed image
- Includes checksums
- Includes release notes

### Docker Hub
- ARM64/ARMv7 images
- For testing purposes
- Pull: `docker pull yourusername/portable-network-tester:latest`

### Direct Download
- Host on own servers
- Provide via CDN
- Include checksum verification

---

## Image Verification

### Verify Checksum
```bash
# After download
sha256sum -c network-tester-*.img.sha256

# Should output: OK
```

### Test in QEMU (Optional)
```bash
# Install QEMU ARM
sudo apt-get install qemu-system-arm

# Boot image
qemu-system-aarch64 \
  -machine raspi3b \
  -cpu cortex-a72 \
  -m 1G \
  -kernel kernel8.img \
  -dtb bcm2710-rpi-3-b.dtb \
  -sd network-tester.img \
  -append "console=ttyAMA0 root=/dev/mmcblk0p2 rw rootwait" \
  -nographic
```

---

## Support

### Getting Help
- Check logs: `/var/log/` and `/opt/network-tester/logs/`
- Open GitHub issue
- Review troubleshooting section

### Reporting Issues
Include:
- Image version/date
- Raspberry Pi model
- Error messages/logs
- Steps to reproduce
