"""
Network reachability testing (ping, traceroute).
"""
import re
import socket
import subprocess
from typing import Optional

from loguru import logger
from testers.connectivity.models import PingResult


class ReachabilityTester:
    """Test network reachability."""

    def get_default_gateway(self) -> Optional[str]:
        """Get the default gateway IP address."""
        try:
            result = subprocess.run(
                ["ip", "route", "show", "default"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                # Parse: default via 192.168.1.1 dev eth0
                match = re.search(r"default via\s+(\S+)", result.stdout)
                if match:
                    return match.group(1)

        except Exception as e:
            logger.error(f"Error getting default gateway: {e}")

        return None

    def ping(self, host: str, count: int = 4, timeout: int = 5) -> PingResult:
        """
        Ping a host.

        Args:
            host: Hostname or IP address to ping
            count: Number of packets to send
            timeout: Timeout in seconds

        Returns:
            PingResult with ping statistics
        """
        logger.info(f"Pinging {host}")

        try:
            # Resolve hostname to IP
            try:
                ip_address = socket.gethostbyname(host)
            except socket.gaierror:
                ip_address = host  # Already an IP or resolution failed

            # Run ping command
            result = subprocess.run(
                ["ping", "-c", str(count), "-W", str(timeout), "-q", host],  # Quiet mode
                capture_output=True,
                text=True,
                timeout=timeout * count + 5,
            )

            # Parse output
            if result.returncode == 0:
                return self._parse_ping_success(host, ip_address, result.stdout, count)
            else:
                return self._parse_ping_failure(host, ip_address, result.stdout, count)

        except subprocess.TimeoutExpired:
            return PingResult(
                success=False,
                host=host,
                ip_address=None,
                packets_sent=count,
                packets_received=0,
                packet_loss_percent=100.0,
                min_rtt_ms=None,
                avg_rtt_ms=None,
                max_rtt_ms=None,
                message="Ping timed out",
            )

        except Exception as e:
            logger.exception(f"Error pinging {host}: {e}")
            return PingResult(
                success=False,
                host=host,
                ip_address=None,
                packets_sent=count,
                packets_received=0,
                packet_loss_percent=100.0,
                min_rtt_ms=None,
                avg_rtt_ms=None,
                max_rtt_ms=None,
                message=f"Error: {str(e)}",
            )

    def _parse_ping_success(
        self, host: str, ip_address: str, output: str, count: int
    ) -> PingResult:
        """Parse successful ping output."""
        # Parse packet statistics
        # Example: "4 packets transmitted, 4 received, 0% packet loss"
        stats_match = re.search(
            r"(\d+) packets transmitted, (\d+) received, ([\d.]+)% packet loss", output
        )

        if stats_match:
            packets_sent = int(stats_match.group(1))
            packets_received = int(stats_match.group(2))
            packet_loss = float(stats_match.group(3))
        else:
            packets_sent = count
            packets_received = count
            packet_loss = 0.0

        # Parse RTT statistics
        # Example: "rtt min/avg/max/mdev = 1.234/2.345/3.456/0.123 ms"
        rtt_match = re.search(
            r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms", output
        )

        if rtt_match:
            min_rtt = float(rtt_match.group(1))
            avg_rtt = float(rtt_match.group(2))
            max_rtt = float(rtt_match.group(3))
        else:
            min_rtt = avg_rtt = max_rtt = None

        message = f"Host reachable - {packets_received}/{packets_sent} packets received"
        if avg_rtt is not None:
            message += f", avg RTT: {avg_rtt:.1f}ms"

        return PingResult(
            success=True,
            host=host,
            ip_address=ip_address,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packet_loss_percent=packet_loss,
            min_rtt_ms=min_rtt,
            avg_rtt_ms=avg_rtt,
            max_rtt_ms=max_rtt,
            message=message,
        )

    def _parse_ping_failure(
        self, host: str, ip_address: str, output: str, count: int
    ) -> PingResult:
        """Parse failed ping output."""
        # Try to extract partial statistics
        stats_match = re.search(
            r"(\d+) packets transmitted, (\d+) received, ([\d.]+)% packet loss", output
        )

        if stats_match:
            packets_sent = int(stats_match.group(1))
            packets_received = int(stats_match.group(2))
            packet_loss = float(stats_match.group(3))
        else:
            packets_sent = count
            packets_received = 0
            packet_loss = 100.0

        # Determine reason
        if "Network is unreachable" in output:
            message = "Network is unreachable"
        elif "Destination Host Unreachable" in output:
            message = "Destination host unreachable"
        elif "Name or service not known" in output:
            message = "Hostname resolution failed"
        else:
            message = f"Ping failed - {packets_received}/{packets_sent} packets received"

        return PingResult(
            success=False,
            host=host,
            ip_address=ip_address if ip_address != host else None,
            packets_sent=packets_sent,
            packets_received=packets_received,
            packet_loss_percent=packet_loss,
            min_rtt_ms=None,
            avg_rtt_ms=None,
            max_rtt_ms=None,
            message=message,
        )

    def traceroute(self, host: str, max_hops: int = 30) -> list[str]:
        """
        Perform traceroute to a host.

        Args:
            host: Hostname or IP to traceroute
            max_hops: Maximum number of hops

        Returns:
            List of hop addresses
        """
        logger.info(f"Traceroute to {host}")

        try:
            result = subprocess.run(
                ["traceroute", "-m", str(max_hops), "-w", "2", host],
                capture_output=True,
                text=True,
                timeout=max_hops * 3,
            )

            # Parse traceroute output
            hops = []
            for line in result.stdout.split("\n"):
                # Look for IP addresses in output
                match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", line)
                if match:
                    hops.append(match.group(1))

            return hops

        except Exception as e:
            logger.error(f"Error running traceroute: {e}")
            return []
