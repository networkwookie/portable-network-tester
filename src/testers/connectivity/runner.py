"""
Connectivity test runner - orchestrates all connectivity tests.
"""
import time
from typing import Callable, Optional

from loguru import logger

from testers.connectivity.ip_services import IPServicesTester
from testers.connectivity.link import LinkTester
from testers.connectivity.models import Status, TestResult
from testers.connectivity.neighbor import NeighborDiscovery
from testers.connectivity.reachability import ReachabilityTester


class ConnectivityTestRunner:
    """Orchestrates connectivity tests in sequence."""

    def __init__(self, interface: Optional[str] = None):
        """
        Initialize test runner.

        Args:
            interface: Network interface to test (auto-detect if None)
        """
        self.interface = interface
        self.link_tester = LinkTester(interface)
        self.neighbor_discovery = NeighborDiscovery()
        self.ip_services = IPServicesTester()
        self.reachability = ReachabilityTester()

    def run_all_tests(
        self, progress_callback: Optional[Callable[[float], None]] = None
    ) -> dict[str, TestResult]:
        """
        Run all connectivity tests in sequence.

        Args:
            progress_callback: Optional callback for progress updates (0.0 to 1.0)

        Returns:
            Dictionary mapping test names to TestResult objects
        """
        results = {}
        total_tests = 6
        current_test = 0

        def update_progress():
            nonlocal current_test
            current_test += 1
            if progress_callback:
                progress_callback(current_test / total_tests)

        logger.info("Starting connectivity test suite")

        # Test 1: Physical Link
        logger.info("Test 1/6: Physical Link Health")
        results["physical_link"] = self._test_physical_link()
        update_progress()

        # Only continue if link is up
        if results["physical_link"].status != Status.PASSED:
            logger.warning("Link is down - skipping remaining tests")
            self._create_skipped_results(results, current_test, total_tests)
            if progress_callback:
                progress_callback(1.0)
            return results

        # Test 2: Neighbor Discovery
        logger.info("Test 2/6: Neighbor Discovery (LLDP)")
        results["neighbor_discovery"] = self._test_neighbor_discovery()
        update_progress()

        # Test 3: DHCP
        logger.info("Test 3/6: DHCP Service")
        results["dhcp"] = self._test_dhcp()
        update_progress()

        # Test 4: DNS
        logger.info("Test 4/6: DNS Service")
        results["dns"] = self._test_dns()
        update_progress()

        # Test 5: Gateway Reachability
        logger.info("Test 5/6: Gateway Reachability")
        results["gateway_ping"] = self._test_gateway_ping()
        update_progress()

        # Test 6: Internet Reachability
        logger.info("Test 6/6: Internet Reachability")
        results["internet_ping"] = self._test_internet_ping()
        update_progress()

        logger.info("Connectivity test suite completed")
        return results

    def _test_physical_link(self) -> TestResult:
        """Test physical link health."""
        start_time = time.time()

        try:
            link_status = self.link_tester.test_link(self.interface)
            duration_ms = (time.time() - start_time) * 1000

            if link_status.link_up:
                return TestResult(
                    name="Physical Link",
                    status=Status.PASSED,
                    message=str(link_status),
                    details={
                        "interface": link_status.interface,
                        "speed_mbps": link_status.speed_mbps,
                        "duplex": link_status.duplex,
                        "carrier": link_status.carrier,
                    },
                    duration_ms=duration_ms,
                )
            else:
                return TestResult(
                    name="Physical Link",
                    status=Status.FAILED,
                    message="Link is down - check cable connection",
                    details={"interface": link_status.interface},
                    duration_ms=duration_ms,
                )

        except Exception as e:
            logger.exception(f"Physical link test failed: {e}")
            return TestResult(
                name="Physical Link",
                status=Status.FAILED,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _test_neighbor_discovery(self) -> TestResult:
        """Test neighbor discovery via LLDP."""
        start_time = time.time()

        try:
            neighbors = self.neighbor_discovery.discover_neighbors(self.interface)
            duration_ms = (time.time() - start_time) * 1000

            if neighbors:
                neighbor_details = [
                    {
                        "chassis_id": n.chassis_id,
                        "system_name": n.system_name,
                        "port_id": n.port_id,
                        "port_description": n.port_description,
                        "vlan": n.vlan,
                    }
                    for n in neighbors
                ]

                message_lines = [f"Found {len(neighbors)} neighbor(s):"]
                for n in neighbors:
                    message_lines.append(f"  • {n}")

                return TestResult(
                    name="Neighbor Discovery",
                    status=Status.PASSED,
                    message="\n".join(message_lines),
                    details={"neighbors": neighbor_details},
                    duration_ms=duration_ms,
                )
            else:
                return TestResult(
                    name="Neighbor Discovery",
                    status=Status.WARNING,
                    message="No LLDP neighbors found (may not be enabled on switch)",
                    duration_ms=duration_ms,
                )

        except Exception as e:
            logger.exception(f"Neighbor discovery failed: {e}")
            return TestResult(
                name="Neighbor Discovery",
                status=Status.WARNING,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _test_dhcp(self) -> TestResult:
        """Test DHCP service."""
        start_time = time.time()

        try:
            dhcp_result = self.ip_services.test_dhcp(self.interface)
            duration_ms = (time.time() - start_time) * 1000

            if dhcp_result.success:
                details_lines = [dhcp_result.message]
                if dhcp_result.gateway:
                    details_lines.append(f"Gateway: {dhcp_result.gateway}")
                if dhcp_result.dns_servers:
                    details_lines.append(f"DNS: {', '.join(dhcp_result.dns_servers)}")

                return TestResult(
                    name="DHCP",
                    status=Status.PASSED,
                    message="\n".join(details_lines),
                    details={
                        "ip_address": dhcp_result.ip_address,
                        "subnet_mask": dhcp_result.subnet_mask,
                        "gateway": dhcp_result.gateway,
                        "dns_servers": dhcp_result.dns_servers,
                    },
                    duration_ms=duration_ms,
                )
            else:
                return TestResult(
                    name="DHCP",
                    status=Status.FAILED,
                    message=dhcp_result.message,
                    duration_ms=duration_ms,
                )

        except Exception as e:
            logger.exception(f"DHCP test failed: {e}")
            return TestResult(
                name="DHCP",
                status=Status.FAILED,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _test_dns(self) -> TestResult:
        """Test DNS service."""
        start_time = time.time()

        try:
            dns_result = self.ip_services.test_dns("google.com")

            if dns_result.success:
                return TestResult(
                    name="DNS",
                    status=Status.PASSED,
                    message=dns_result.message,
                    details={
                        "query": dns_result.query,
                        "resolved_ips": dns_result.resolved_ips,
                        "response_time_ms": dns_result.response_time_ms,
                    },
                    duration_ms=dns_result.response_time_ms,
                )
            else:
                return TestResult(
                    name="DNS",
                    status=Status.FAILED,
                    message=dns_result.message,
                    duration_ms=dns_result.response_time_ms,
                )

        except Exception as e:
            logger.exception(f"DNS test failed: {e}")
            return TestResult(
                name="DNS",
                status=Status.FAILED,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _test_gateway_ping(self) -> TestResult:
        """Test gateway reachability."""
        start_time = time.time()

        try:
            gateway = self.reachability.get_default_gateway()

            if not gateway:
                return TestResult(
                    name="Gateway Ping",
                    status=Status.FAILED,
                    message="No default gateway found",
                    duration_ms=(time.time() - start_time) * 1000,
                )

            ping_result = self.reachability.ping(gateway, count=4)

            if ping_result.success:
                return TestResult(
                    name="Gateway Ping",
                    status=Status.PASSED,
                    message=f"Gateway {gateway}: {ping_result.message}",
                    details={
                        "gateway": gateway,
                        "packets_sent": ping_result.packets_sent,
                        "packets_received": ping_result.packets_received,
                        "avg_rtt_ms": ping_result.avg_rtt_ms,
                    },
                    duration_ms=(time.time() - start_time) * 1000,
                )
            else:
                return TestResult(
                    name="Gateway Ping",
                    status=Status.FAILED,
                    message=f"Gateway {gateway}: {ping_result.message}",
                    duration_ms=(time.time() - start_time) * 1000,
                )

        except Exception as e:
            logger.exception(f"Gateway ping failed: {e}")
            return TestResult(
                name="Gateway Ping",
                status=Status.FAILED,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _test_internet_ping(self) -> TestResult:
        """Test internet reachability."""
        start_time = time.time()

        try:
            # Ping a reliable public DNS server
            ping_result = self.reachability.ping("8.8.8.8", count=4)

            if ping_result.success:
                return TestResult(
                    name="Internet Ping",
                    status=Status.PASSED,
                    message=f"Internet reachable (8.8.8.8): {ping_result.message}",
                    details={
                        "host": "8.8.8.8",
                        "packets_sent": ping_result.packets_sent,
                        "packets_received": ping_result.packets_received,
                        "avg_rtt_ms": ping_result.avg_rtt_ms,
                    },
                    duration_ms=(time.time() - start_time) * 1000,
                )
            else:
                return TestResult(
                    name="Internet Ping",
                    status=Status.FAILED,
                    message=f"Internet not reachable: {ping_result.message}",
                    duration_ms=(time.time() - start_time) * 1000,
                )

        except Exception as e:
            logger.exception(f"Internet ping failed: {e}")
            return TestResult(
                name="Internet Ping",
                status=Status.FAILED,
                message=f"Error: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )

    def _create_skipped_results(
        self, results: dict[str, TestResult], current: int, total: int
    ) -> None:
        """Create skipped results for remaining tests."""
        test_names = ["neighbor_discovery", "dhcp", "dns", "gateway_ping", "internet_ping"]

        for test_name in test_names:
            if test_name not in results:
                results[test_name] = TestResult(
                    name=test_name.replace("_", " ").title(),
                    status=Status.PENDING,
                    message="Skipped due to link failure",
                    duration_ms=0.0,
                )
