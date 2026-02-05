"""
IP services testing (DHCP, DNS).
"""
import socket
import subprocess
import time
from typing import Optional
from loguru import logger

from tests.connectivity.models import DHCPResult, DNSResult


class IPServicesTester:
    """Test IP services like DHCP and DNS."""
    
    def test_dhcp(self, interface: Optional[str] = None) -> DHCPResult:
        """
        Test DHCP service by checking current lease.
        
        Note: This checks if interface has DHCP-assigned address,
        not performing a new DHCP request (which would disrupt connectivity).
        
        Args:
            interface: Interface to check
            
        Returns:
            DHCPResult with DHCP information
        """
        logger.info("Testing DHCP configuration")
        
        try:
            # Check dhclient lease file
            result = self._check_dhclient_lease(interface)
            if result:
                return result
            
            # Fallback: check if interface has IP via DHCP
            return self._check_interface_dhcp_config(interface)
            
        except Exception as e:
            logger.exception(f"Error testing DHCP: {e}")
            return DHCPResult(
                success=False,
                ip_address=None,
                subnet_mask=None,
                gateway=None,
                dns_servers=[],
                lease_time=None,
                message=f"Error: {str(e)}"
            )
    
    def _check_dhclient_lease(self, interface: Optional[str]) -> Optional[DHCPResult]:
        """Check dhclient lease file."""
        lease_files = [
            f"/var/lib/dhcp/dhclient.{interface}.leases" if interface else None,
            "/var/lib/dhcp/dhclient.leases",
            "/var/lib/dhclient/dhclient.leases"
        ]
        
        for lease_file in lease_files:
            if not lease_file:
                continue
            
            try:
                with open(lease_file, "r") as f:
                    content = f.read()
                
                # Parse lease information
                ip_addr = self._extract_lease_value(content, "fixed-address")
                subnet = self._extract_lease_value(content, "subnet-mask")
                gateway = self._extract_lease_value(content, "routers")
                dns_str = self._extract_lease_value(content, "domain-name-servers")
                
                dns_servers = dns_str.split(",") if dns_str else []
                dns_servers = [d.strip() for d in dns_servers]
                
                if ip_addr:
                    return DHCPResult(
                        success=True,
                        ip_address=ip_addr,
                        subnet_mask=subnet,
                        gateway=gateway,
                        dns_servers=dns_servers,
                        lease_time=None,
                        message=f"DHCP active - IP: {ip_addr}"
                    )
            
            except FileNotFoundError:
                continue
            except Exception as e:
                logger.error(f"Error reading lease file {lease_file}: {e}")
        
        return None
    
    def _extract_lease_value(self, content: str, key: str) -> Optional[str]:
        """Extract value from dhclient lease file."""
        import re
        pattern = rf'{key}\s+([^;]+);'
        match = re.search(pattern, content)
        if match:
            return match.group(1).strip().strip('"')
        return None
    
    def _check_interface_dhcp_config(self, interface: Optional[str]) -> DHCPResult:
        """Check if interface appears to be configured via DHCP."""
        try:
            result = subprocess.run(
                ["ip", "addr", "show", interface] if interface else ["ip", "addr"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and "inet " in result.stdout:
                # Has IP address - assume DHCP if we can't verify otherwise
                import re
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', result.stdout)
                ip_addr = match.group(1) if match else None
                
                return DHCPResult(
                    success=True,
                    ip_address=ip_addr,
                    subnet_mask=None,
                    gateway=None,
                    dns_servers=[],
                    lease_time=None,
                    message=f"Interface has IP address (likely DHCP): {ip_addr}"
                )
        
        except Exception as e:
            logger.error(f"Error checking interface config: {e}")
        
        return DHCPResult(
            success=False,
            ip_address=None,
            subnet_mask=None,
            gateway=None,
            dns_servers=[],
            lease_time=None,
            message="No DHCP configuration detected"
        )
    
    def test_dns(self, hostname: str = "google.com", dns_server: Optional[str] = None) -> DNSResult:
        """
        Test DNS resolution.
        
        Args:
            hostname: Hostname to resolve
            dns_server: DNS server to query (system default if None)
            
        Returns:
            DNSResult with resolution information
        """
        logger.info(f"Testing DNS resolution for {hostname}")
        
        start_time = time.time()
        
        try:
            # Use socket.getaddrinfo for resolution
            result = socket.getaddrinfo(hostname, None, socket.AF_INET)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Extract unique IP addresses
            ips = list(set([addr[4][0] for addr in result]))
            
            return DNSResult(
                success=True,
                query=hostname,
                resolved_ips=ips,
                response_time_ms=elapsed_ms,
                message=f"Resolved to {', '.join(ips)} in {elapsed_ms:.1f}ms"
            )
        
        except socket.gaierror as e:
            elapsed_ms = (time.time() - start_time) * 1000
            return DNSResult(
                success=False,
                query=hostname,
                resolved_ips=[],
                response_time_ms=elapsed_ms,
                message=f"DNS resolution failed: {str(e)}"
            )
        
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.exception(f"Error testing DNS: {e}")
            return DNSResult(
                success=False,
                query=hostname,
                resolved_ips=[],
                response_time_ms=elapsed_ms,
                message=f"Error: {str(e)}"
            )
