# Image Building Quick Reference

## TL;DR - Just Give Me an Image!

### Option 1: Download Pre-built (Easiest)
```bash
# Go to GitHub Releases
https://github.com/yourusername/portable-network-tester/releases

# Download: network-tester-*-raspios-arm64.img.zip
# Write to SD card with Raspberry Pi Imager or dd
```

### Option 2: Build Yourself (10 minutes)
```bash
# 1. Get base image
wget https://downloads.raspberrypi.org/raspios_lite_arm64_latest
unxz *.img.xz

# 2. Customize
sudo ./scripts/customize-image.sh raspios-*.img

# 3. Write to SD
sudo dd if=*-network-tester.img of=/dev/sdX bs=4M status=progress
```

---

## Build Methods Comparison

| Method | Time | Complexity | When to Use |
|--------|------|------------|-------------|
| **Download pre-built** | 0 min | ⭐ Easy | Production deployment |
| **Customize existing** | 10 min | ⭐⭐ Medium | Quick custom build |
| **GitHub Actions** | 20 min | ⭐ Easy | Automated releases |
| **pi-gen (full build)** | 60 min | ⭐⭐⭐ Hard | Complete customization |
| **Packer** | 30 min | ⭐⭐⭐ Hard | Infrastructure as code |

---

## Commands Cheat Sheet

### Download Base Image
```bash
# 64-bit Lite (recommended)
wget https://downloads.raspberrypi.org/raspios_lite_arm64_latest -O raspios.img.xz
xz -d raspios.img.xz

# 32-bit Lite
wget https://downloads.raspberrypi.org/raspios_lite_armhf_latest -O raspios.img.xz
```

### Customize Image
```bash
sudo ./scripts/customize-image.sh raspios.img
# Output: raspios-network-tester.img
```

### Build from Scratch
```bash
./scripts/build-image.sh
# Output: build/images/network-tester-*.img.xz
```

### Write to SD Card
```bash
# Linux/Mac
sudo dd if=network-tester.img of=/dev/sdX bs=4M status=progress conv=fsync

# Find device
lsblk

# Verify
sudo fdisk -l /dev/sdX
```

### Verify Image
```bash
# Check file integrity
sha256sum -c network-tester.img.sha256

# Mount and inspect
sudo losetup -fP network-tester.img
sudo mount /dev/loop0p2 /mnt
ls -la /mnt/opt/network-tester
sudo umount /mnt
sudo losetup -d /dev/loop0
```

---

## GitHub Actions Workflow

### Trigger Release Build
```bash
# Create version tag
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# GitHub Actions will:
# 1. Build image
# 2. Compress
# 3. Create release
# 4. Upload artifacts
```

### Manual Build Trigger
```
1. Go to Actions tab
2. Select "Build Raspberry Pi Images"
3. Click "Run workflow"
4. Download from Artifacts
```

---

## First Boot Checklist

After writing image to SD card:

- [ ] Insert SD card into Pi 4
- [ ] Connect 7" touchscreen
- [ ] Connect Ethernet cable
- [ ] Power on
- [ ] Wait 5-10 minutes (first boot installs dependencies)
- [ ] Application should auto-start
- [ ] Test connectivity test feature

### Troubleshooting First Boot

```bash
# SSH into Pi
ssh pi@network-tester.local
# Default password: raspberry

# Check installation log
tail -f /var/log/network-tester-install.log

# Check service status
sudo systemctl status network-tester

# View application log
tail -f /opt/network-tester/logs/network_tester.log

# Manual start
cd /opt/network-tester
./venv/bin/python src/main.py
```

---

## Image Specifications

### Minimum Requirements
- **SD Card**: 8GB (16GB recommended)
- **Pi Model**: Raspberry Pi 4 Model B (or Pi 400, Pi 5)
- **Display**: 7" touchscreen (800x480)
- **Network**: Ethernet or WiFi

### Image Contents
- **OS**: Raspberry Pi OS Lite (64-bit, Bookworm)
- **Size**: ~3.5GB uncompressed
- **Python**: 3.11+
- **Auto-start**: Yes (systemd service)
- **SSH**: Enabled
- **Default user**: pi / raspberry
- **Hostname**: network-tester

---

## Common Issues

### "Permission denied" during build
```bash
# Must run with sudo
sudo ./scripts/customize-image.sh raspios.img
```

### "Device or resource busy" during unmount
```bash
# Force unmount
sudo umount -l /mnt
sudo losetup -d /dev/loop0
```

### SD card not detected
```bash
# Check for proper device
lsblk
# Look for removable disk (usually /dev/sdX or /dev/mmcblkX)

# Ensure not mounted
sudo umount /dev/sdX*
```

### Application doesn't start on first boot
```bash
# SSH in and check
ssh pi@network-tester.local

# Check if installation completed
ls -la /opt/network-tester/.installed

# If not, run manually
sudo /opt/network-tester-install.sh
```

---

## Advanced: Custom Configuration

### Pre-configure WiFi
```bash
# Before unmounting image
sudo nano /mnt/boot/wpa_supplicant.conf

# Add:
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
network={
    ssid="YourNetwork"
    psk="YourPassword"
}
```

### Change Default Password
```bash
# In mounted image
sudo chroot /mnt
echo "pi:newpassword" | chpasswd
exit
```

### Modify Application Config
```bash
# Edit config before unmounting
sudo nano /mnt/opt/network-tester/config.yml
```

---

## Release Process

1. **Update version** in `pyproject.toml`
2. **Commit changes**
3. **Create tag**: `git tag -a v1.0.0 -m "Release 1.0.0"`
4. **Push**: `git push origin main && git push origin v1.0.0`
5. **Wait for build** (GitHub Actions)
6. **Download from Releases** page
7. **Test image** on actual hardware
8. **Announce release**

---

## Resources

- [IMAGE_BUILDING.md](IMAGE_BUILDING.md) - Full documentation
- [Raspberry Pi Imager](https://www.raspberrypi.org/software/) - Write images
- [balenaEtcher](https://www.balena.io/etcher/) - Alternative writer
- [GitHub Releases](https://github.com/yourusername/portable-network-tester/releases) - Pre-built images
