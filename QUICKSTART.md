# Quick Start Guide

## For Developers

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/portable-network-tester.git
cd portable-network-tester
```

### 2. Setup Development Environment
```bash
# Run setup script (Linux/Raspberry Pi)
./scripts/setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

### 3. Run the Application
```bash
source venv/bin/activate
python src/main.py
```

### 4. Run Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -m unit

# With coverage
pytest --cov=src --cov-report=html
```

### 5. Code Quality Checks
```bash
# Format
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## For Raspberry Pi Production

### 1. Hardware Setup
- Connect Raspberry Pi 4 Model B
- Attach 7-inch touchscreen
- Connect network cable or WiFi
- Power on

### 2. Software Installation
```bash
cd /home/pi
git clone https://github.com/yourusername/portable-network-tester.git
cd portable-network-tester
./scripts/setup.sh
```

### 3. Configure for Production
```bash
# Edit config
cp config.example.yml config.yml
nano config.yml

# Set fullscreen: true in ui section
```

### 4. Install as Service (Auto-start)
```bash
sudo cp scripts/network-tester.service /etc/systemd/system/
sudo systemctl enable network-tester
sudo systemctl start network-tester

# Check status
sudo systemctl status network-tester

# View logs
journalctl -u network-tester -f
```

### 5. Manual Run (Testing)
```bash
source venv/bin/activate
python src/main.py
```

## Using the Application

### Main Menu
The main menu presents three options:
1. **Connectivity Test** - Network diagnostics
2. **Speed Test** - Coming soon
3. **Packet Capture** - Coming soon

### Connectivity Test
Tests network connectivity in this order:
1. Physical link health (speed, duplex)
2. Neighbor discovery (LLDP)
3. DHCP service
4. DNS service
5. Gateway reachability
6. Internet reachability

Each test displays:
- ✓ Passed (green)
- ✗ Failed (red)
- ⚠ Warning (yellow)
- Detailed results

## VSCode Setup

### 1. Open in VSCode
```bash
code portable-network-tester
```

### 2. Select Python Interpreter
- Press `Ctrl+Shift+P`
- Type "Python: Select Interpreter"
- Choose `./venv/bin/python`

### 3. Recommended Extensions
VSCode will prompt to install recommended extensions:
- Python
- Pylance
- Black Formatter
- Ruff
- YAML
- GitLens

### 4. Run/Debug
- Press `F5` to start debugging
- Set breakpoints by clicking left of line numbers
- Use Debug Console for interactive debugging

## Common Issues

### Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall in editable mode
pip install -e .
```

### Permission Errors (Raspberry Pi)
```bash
# Add user to netdev group for network access
sudo usermod -a -G netdev $USER

# Reboot for changes to take effect
sudo reboot
```

### Display Issues
```bash
# Set DISPLAY environment variable
export DISPLAY=:0

# Or in systemd service file (already configured)
```

### LLDP Not Working
```bash
# Ensure lldpd is running
sudo systemctl status lldpd
sudo systemctl start lldpd

# Check LLDP data
sudo lldpcli show neighbors
```

## Next Steps

- Read [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines
- Check [README.md](README.md) for detailed documentation
- Review issues on GitHub
- Join discussions for feature requests

## Getting Help

- Open an issue on GitHub
- Check existing issues for solutions
- Review logs: `tail -f logs/network_tester.log`
