# Portable Network Tester

An open-source, portable network diagnostic tool built for Raspberry Pi 4 Model B with a 7-inch touchscreen display.

## Features

- **Connectivity Test**: Physical link health, neighbor discovery, IP services, and reachability tests
- **Speed Test**: Network bandwidth testing (coming soon)
- **Packet Capture**: Network traffic analysis (coming soon)

## Hardware Requirements

- Raspberry Pi 4 Model B
- 7-inch touchscreen display
- Network connectivity (Ethernet or WiFi)

## Software Architecture

```
portable-network-tester/
├── src/
│   ├── ui/              # Touch-optimized UI (Kivy)
│   ├── tests/           # Test modules
│   │   ├── connectivity/
│   │   ├── speedtest/
│   │   └── capture/
│   ├── utils/           # Common utilities
│   └── main.py          # Application entry point
├── tests/               # Test suite
│   ├── unit/
│   ├── integration/
│   └── system/
├── scripts/             # Setup and deployment scripts
└── docs/                # Documentation
```

## Quick Start with Pre-built Image

The easiest way to get started is using a pre-built Raspberry Pi OS image:

1. **Download the latest image** from [Releases](https://github.com/yourusername/portable-network-tester/releases)
2. **Write to SD card** using [Raspberry Pi Imager](https://www.raspberrypi.org/software/) or `dd`
3. **Insert SD card** into Raspberry Pi 4
4. **Power on** - Application auto-starts (first boot takes 5-10 minutes)

See [Image Building Guide](docs/IMAGE_BUILDING.md) for details on creating custom images.

## Installation from Source

### Prerequisites

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Python 3.11+
sudo apt-get install python3 python3-pip python3-venv -y

# Install system dependencies
sudo apt-get install -y \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    pkg-config libgl1-mesa-dev libgles2-mesa-dev \
    python3-setuptools libgstreamer1.0-dev git-core \
    gstreamer1.0-plugins-{bad,base,good,ugly} \
    gstreamer1.0-{omx,alsa} python3-dev libmtdev-dev \
    xclip xsel libjpeg-dev tcpdump net-tools ethtool lldpd

# Enable LLDP daemon for neighbor discovery
sudo systemctl enable lldpd
sudo systemctl start lldpd
```

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/portable-network-tester.git
cd portable-network-tester

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

### Development Setup

```bash
# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .
black --check .
mypy src/
```

## Usage

### Running the Application

```bash
# Activate virtual environment
source venv/bin/activate

# Run application
python src/main.py
```

### Running as a Service (Auto-start on Boot)

```bash
# Install as systemd service
sudo cp scripts/network-tester.service /etc/systemd/system/
sudo systemctl enable network-tester
sudo systemctl start network-tester
```

## Development

### Project Structure

- **src/ui/**: Kivy-based touchscreen interface
- **src/tests/connectivity/**: Network connectivity testing logic
- **src/utils/**: Shared utilities (network helpers, logging, etc.)
- **tests/**: Comprehensive test suite

### Adding New Test Modules

1. Create module in `src/tests/<module_name>/`
2. Implement test logic with clear interface
3. Add UI screen in `src/ui/screens/`
4. Write unit, integration, and system tests
5. Update documentation

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# System tests (requires hardware or mocks)
pytest tests/system/

# With coverage
pytest --cov=src --cov-report=html
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type checking
mypy src/
```

## CI/CD Pipeline

GitHub Actions automatically:
- Runs linting (ruff, black, mypy)
- Executes unit tests
- Runs integration tests
- Executes system tests (mocked)
- Generates coverage reports
- Builds release artifacts
- **Builds bootable Raspberry Pi images** (on version tags)

See [Image Building Guide](docs/IMAGE_BUILDING.md) for creating custom images.

## Building Custom Images

Create bootable Raspberry Pi OS images with Network Tester pre-installed:

### Quick Method (Recommended)
```bash
# Download base Raspberry Pi OS image
wget https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64-lite.img.xz
xz -d *.img.xz

# Customize with Network Tester
sudo ./scripts/customize-image.sh 2024-03-15-raspios-bookworm-arm64-lite.img

# Write to SD card
sudo dd if=*-network-tester.img of=/dev/sdX bs=4M status=progress conv=fsync
```

### Automated Builds
Images are automatically built via GitHub Actions when you push version tags:
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

See [docs/IMAGE_BUILDING.md](docs/IMAGE_BUILDING.md) for full documentation on:
- Multiple build methods (customize, pi-gen, Packer)
- GitHub Actions automation
- Image verification
- Troubleshooting

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Uses Kivy for touchscreen UI
- Leverages scapy for packet operations
- Utilizes pyroute2 for network interface management
- LLDP support via lldpd
