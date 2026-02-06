"""
LLDP neighbor discovery.
"""
import json
import subprocess
from typing import Optional

from loguru import logger

from testers.connectivity.models import NeighborInfo


class NeighborDiscovery:
    """Discover network neighbors using LLDP."""

    def discover_neighbors(self, interface: Optional[str] = None) -> list[NeighborInfo]:
        """
        Discover neighbors using LLDP.

        Args:
            interface: Interface to check (all if None)

        Returns:
            List of discovered neighbors
        """
        neighbors = []

        # Try lldpcli (from lldpd)
        neighbors.extend(self._discover_with_lldpcli(interface))

        return neighbors

    def _discover_with_lldpcli(self, interface: Optional[str] = None) -> list[NeighborInfo]:
        """Discover neighbors using lldpcli."""
        try:
            cmd = ["lldpcli", "show", "neighbors", "-f", "json"]
            if interface:
                cmd.extend(["-p", interface])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                logger.warning(f"lldpcli failed: {result.stderr}")
                return []

            return self._parse_lldpcli_json(result.stdout)

        except FileNotFoundError:
            logger.warning("lldpcli not found - install lldpd for neighbor discovery")
            return []
        except Exception as e:
            logger.error(f"Error discovering neighbors: {e}")
            return []

    def _parse_lldpcli_json(self, json_str: str) -> list[NeighborInfo]:
        """Parse lldpcli JSON output."""
        neighbors = []

        try:
            data = json.loads(json_str)

            # lldpcli JSON structure: {"lldp": {"interface": {...}}}
            if "lldp" not in data:
                return neighbors

            lldp_data = data["lldp"]
            if "interface" not in lldp_data:
                return neighbors

            interfaces = lldp_data["interface"]
            if isinstance(interfaces, dict):
                interfaces = [interfaces]

            for iface_data in interfaces:
                if not isinstance(iface_data, dict):
                    continue

                iface_name = list(iface_data.keys())[0] if iface_data else None
                if not iface_name:
                    continue

                iface_info = iface_data[iface_name]
                if "chassis" not in iface_info or "port" not in iface_info:
                    continue

                chassis = iface_info["chassis"]
                port = iface_info["port"]

                # Extract VLAN if present
                vlan = None
                if "vlan" in iface_info:
                    vlan_data = iface_info["vlan"]
                    if isinstance(vlan_data, dict) and "vlan-id" in vlan_data:
                        try:
                            vlan = int(vlan_data["vlan-id"])
                        except (ValueError, TypeError):
                            pass

                neighbor = NeighborInfo(
                    interface=iface_name,
                    chassis_id=chassis.get("id", {}).get("value", "unknown"),
                    system_name=chassis.get("name", {}).get("value"),
                    port_id=port.get("id", {}).get("value", "unknown"),
                    port_description=port.get("descr", {}).get("value"),
                    vlan=vlan,
                )

                neighbors.append(neighbor)
                logger.info(f"Discovered neighbor: {neighbor}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse lldpcli JSON: {e}")
        except Exception as e:
            logger.error(f"Error parsing neighbor info: {e}")

        return neighbors
