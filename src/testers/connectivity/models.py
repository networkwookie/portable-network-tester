"""
Data models for connectivity tests.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class Status(Enum):
    """Status of a test."""

    PENDING = "Pending"
    RUNNING = "Running"
    PASSED = "Passed"
    FAILED = "Failed"
    WARNING = "Warning"


@dataclass
class TestResult:
    """Result of a connectivity test."""

    name: str
    status: Status
    message: str
    details: Optional[dict[str, Any]] = None
    duration_ms: float = 0.0

    def __str__(self) -> str:
        return f"{self.name}: {self.status.value} - {self.message}"


@dataclass
class LinkStatus:
    """Physical link status information."""

    interface: str
    link_up: bool
    speed_mbps: Optional[int]
    duplex: Optional[str]
    carrier: bool

    def __str__(self) -> str:
        if not self.link_up:
            return f"{self.interface}: Link Down"
        return (
            f"{self.interface}: Link Up - "
            f"{self.speed_mbps or '?'}Mbps {self.duplex or 'unknown'}"
        )


@dataclass
class NeighborInfo:
    """LLDP neighbor information."""

    interface: str
    chassis_id: str
    system_name: Optional[str]
    port_id: str
    port_description: Optional[str]
    vlan: Optional[int]

    def __str__(self) -> str:
        name = self.system_name or self.chassis_id
        return f"{name} on port {self.port_id}"


@dataclass
class DHCPResult:
    """DHCP service test result."""

    success: bool
    ip_address: Optional[str]
    subnet_mask: Optional[str]
    gateway: Optional[str]
    dns_servers: list[str]
    lease_time: Optional[int]
    message: str


@dataclass
class DNSResult:
    """DNS service test result."""

    success: bool
    query: str
    resolved_ips: list[str]
    response_time_ms: float
    message: str


@dataclass
class PingResult:
    """Ping test result."""

    success: bool
    host: str
    ip_address: Optional[str]
    packets_sent: int
    packets_received: int
    packet_loss_percent: float
    min_rtt_ms: Optional[float]
    avg_rtt_ms: Optional[float]
    max_rtt_ms: Optional[float]
    message: str
