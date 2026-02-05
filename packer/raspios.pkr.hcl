packer {
  required_plugins {
    arm-image = {
      version = ">= 0.2.7"
      source  = "github.com/solo-io/arm-image"
    }
  }
}

variable "raspberry_pi_os_image_url" {
  type    = string
  default = "https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2024-03-15/2024-03-15-raspios-bookworm-arm64-lite.img.xz"
}

variable "image_checksum" {
  type    = string
  default = "sha256:0ebdd825828c98aa7c82e88e6ec3e2f8bb2e2d27c1d3c8d1a5f5b5f5d5f5d5f5"
}

variable "target_image_size" {
  type    = string
  default = "4G"
}

source "arm-image" "raspios" {
  iso_url           = var.raspberry_pi_os_image_url
  iso_checksum      = var.image_checksum
  target_image_size = var.target_image_size
  image_type        = "raspberrypi"
  
  # Output configuration
  output_filename = "network-tester-raspios.img"
}

build {
  sources = ["source.arm-image.raspios"]

  # Copy application files
  provisioner "file" {
    source      = "../src"
    destination = "/tmp/"
  }

  provisioner "file" {
    source      = "../tests"
    destination = "/tmp/"
  }

  provisioner "file" {
    source      = "../pyproject.toml"
    destination = "/tmp/"
  }

  provisioner "file" {
    source      = "../README.md"
    destination = "/tmp/"
  }

  provisioner "file" {
    source      = "../config.example.yml"
    destination = "/tmp/"
  }

  provisioner "file" {
    source      = "../scripts"
    destination = "/tmp/"
  }

  # Run installation script
  provisioner "shell" {
    inline = [
      "sudo apt-get update",
      "sudo apt-get upgrade -y",
      
      # Install system dependencies
      "sudo apt-get install -y python3 python3-pip python3-venv",
      "sudo apt-get install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev",
      "sudo apt-get install -y pkg-config libgl1-mesa-dev libgles2-mesa-dev",
      "sudo apt-get install -y python3-setuptools libgstreamer1.0-dev git-core",
      "sudo apt-get install -y gstreamer1.0-plugins-bad gstreamer1.0-plugins-base",
      "sudo apt-get install -y gstreamer1.0-plugins-good gstreamer1.0-plugins-ugly",
      "sudo apt-get install -y gstreamer1.0-omx gstreamer1.0-alsa",
      "sudo apt-get install -y python3-dev libmtdev-dev xclip xsel libjpeg-dev",
      "sudo apt-get install -y tcpdump net-tools ethtool lldpd iputils-ping traceroute",
      
      # Create application directory
      "sudo mkdir -p /opt/network-tester",
      "sudo mv /tmp/src /opt/network-tester/",
      "sudo mv /tmp/tests /opt/network-tester/",
      "sudo mv /tmp/pyproject.toml /opt/network-tester/",
      "sudo mv /tmp/README.md /opt/network-tester/",
      "sudo mv /tmp/config.example.yml /opt/network-tester/config.yml",
      "sudo mv /tmp/scripts /opt/network-tester/",
      
      # Create virtual environment and install
      "cd /opt/network-tester",
      "sudo python3 -m venv venv",
      "sudo /opt/network-tester/venv/bin/pip install --upgrade pip",
      "sudo /opt/network-tester/venv/bin/pip install -e .",
      
      # Set permissions
      "sudo chown -R pi:pi /opt/network-tester",
      
      # Enable LLDP
      "sudo systemctl enable lldpd",
      
      # Install systemd service
      "sudo cp /opt/network-tester/scripts/network-tester.service /etc/systemd/system/",
      "sudo sed -i 's|/home/pi/portable-network-tester|/opt/network-tester|g' /etc/systemd/system/network-tester.service",
      "sudo systemctl enable network-tester",
      
      # Configure auto-login for pi user
      "sudo mkdir -p /etc/systemd/system/getty@tty1.service.d",
      "echo '[Service]' | sudo tee /etc/systemd/system/getty@tty1.service.d/autologin.conf",
      "echo 'ExecStart=' | sudo tee -a /etc/systemd/system/getty@tty1.service.d/autologin.conf",
      "echo 'ExecStart=-/sbin/agetty --autologin pi --noclear %I $TERM' | sudo tee -a /etc/systemd/system/getty@tty1.service.d/autologin.conf",
      
      # Configure X11 auto-start
      "mkdir -p /home/pi/.config/autostart",
      "echo '[Desktop Entry]' > /home/pi/.config/autostart/network-tester.desktop",
      "echo 'Type=Application' >> /home/pi/.config/autostart/network-tester.desktop",
      "echo 'Name=Network Tester' >> /home/pi/.config/autostart/network-tester.desktop",
      "echo 'Exec=/opt/network-tester/venv/bin/python /opt/network-tester/src/main.py' >> /home/pi/.config/autostart/network-tester.desktop",
      
      # Clean up
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      
      # Create info file
      "echo 'Network Tester Image' | sudo tee /opt/network-tester/IMAGE_INFO",
      "echo 'Built: '$(date) | sudo tee -a /opt/network-tester/IMAGE_INFO",
      "echo 'Version: '$(cat /opt/network-tester/pyproject.toml | grep version | head -1 | cut -d'\"' -f2) | sudo tee -a /opt/network-tester/IMAGE_INFO"
    ]
  }

  # Final configuration
  provisioner "shell" {
    inline = [
      # Set hostname
      "echo 'network-tester' | sudo tee /etc/hostname",
      "sudo sed -i 's/127.0.1.1.*/127.0.1.1\tnetwork-tester/g' /etc/hosts",
      
      # Enable SSH (optional)
      "sudo systemctl enable ssh",
      
      # Disable unnecessary services to save resources
      "sudo systemctl disable bluetooth.service",
      "sudo systemctl disable hciuart.service",
      
      # Configure fullscreen mode
      "sudo sed -i 's/fullscreen: false/fullscreen: true/g' /opt/network-tester/config.yml"
    ]
  }
}
