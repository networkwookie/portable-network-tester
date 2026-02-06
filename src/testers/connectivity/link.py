"""
Physical link health testing.
"""
import re
import subprocess
from typing import Optional

from loguru import logger

from testers.connectivity.models import LinkStatus


class LinkTester:
    """Test physical link health."""

    def __init__(self, interface: Optional[str] = None):
        """
        Initialize link tester.

        Args:
            interface: Network interface to test (auto-detect if None)
        """
        self.interface = interface

    def get_default_interface(self) -> Optional[str]:
        """Get the default network interface."""
        try:
            # Get default route interface
            result = subprocess.run(
                ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                # Parse: default via 192.168.1.1 dev eth0
                match = re.search(r"dev\s+(\S+)", result.stdout)
                if match:
                    return match.group(1)

            # Fallback: get first non-loopback interface
            result = subprocess.run(
                ["ip", "link", "show"], capture_output=True, text=True, timeout=5
            )

            for line in result.stdout.split("\n"):
                if ": " in line and "lo:" not in line:
                    match = re.search(r"^\d+:\s+(\S+):", line)
                    if match:
                        return match.group(1)

        except Exception as e:
            logger.error(f"Error getting default interface: {e}")

        return None

    def test_link(self, interface: Optional[str] = None) -> LinkStatus:
        """
        Test physical link status.

        Args:
            interface: Interface to test (uses default if None)

        Returns:
            LinkStatus with link information
        """
        iface = interface or self.interface or self.get_default_interface()

        if not iface:
            logger.error("No network interface found")
            return LinkStatus(
                interface="unknown", link_up=False, speed_mbps=None, duplex=None, carrier=False
            )

        logger.info(f"Testing link on interface: {iface}")

        try:
            # Check carrier state
            carrier = self._check_carrier(iface)

            # Get link info from ethtool
            speed, duplex = self._get_ethtool_info(iface)

            # Check if link is operationally up
            link_up = self._check_link_up(iface)

            return LinkStatus(
                interface=iface,
                link_up=link_up and carrier,
                speed_mbps=speed,
                duplex=duplex,
                carrier=carrier,
            )

        except Exception as e:
            logger.exception(f"Error testing link: {e}")
            return LinkStatus(
                interface=iface, link_up=False, speed_mbps=None, duplex=None, carrier=False
            )

    def _check_carrier(self, interface: str) -> bool:
        """Check if interface has carrier signal."""
        try:
            with open(f"/sys/class/net/{interface}/carrier") as f:
                return f.read().strip() == "1"
        except (FileNotFoundError, PermissionError):
            # Fallback to ip command
            try:
                result = subprocess.run(
                    ["ip", "link", "show", interface], capture_output=True, text=True, timeout=5
                )
                return "state UP" in result.stdout
            except Exception:
                return False

    def _check_link_up(self, interface: str) -> bool:
        """Check if interface is operationally up."""
        try:
            result = subprocess.run(
                ["ip", "link", "show", interface], capture_output=True, text=True, timeout=5
            )
            return "state UP" in result.stdout
        except Exception as e:
            logger.error(f"Error checking link state: {e}")
            return False

    def _get_ethtool_info(self, interface: str) -> tuple[Optional[int], Optional[str]]:
        """
        Get speed and duplex from ethtool.

        Returns:
            Tuple of (speed_mbps, duplex)
        """
        try:
            result = subprocess.run(
                ["ethtool", interface], capture_output=True, text=True, timeout=5
            )

            if result.returncode != 0:
                return None, None

            speed = None
            duplex = None

            for line in result.stdout.split("\n"):
                if "Speed:" in line:
                    match = re.search(r"(\d+)Mb/s", line)
                    if match:
                        speed = int(match.group(1))

                if "Duplex:" in line:
                    match = re.search(r"Duplex:\s+(\w+)", line)
                    if match:
                        duplex = match.group(1)

            return speed, duplex

        except FileNotFoundError:
            logger.warning("ethtool not found, skipping speed/duplex detection")
            return None, None
        except Exception as e:
            logger.error(f"Error getting ethtool info: {e}")
            return None, None
