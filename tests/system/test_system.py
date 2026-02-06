"""
System tests for UI and application flow.
"""
import os
from unittest.mock import Mock, patch

import pytest

# Set environment variable before importing Kivy
os.environ["KIVY_NO_ARGS"] = "1"
os.environ["KIVY_USE_DEFAULTCONFIG"] = "1"


@pytest.mark.system
class TestApplicationSystem:
    """System tests for the application."""

    @patch("ui.app.Window")
    def test_app_initialization(self, mock_window):
        """Test application initializes correctly."""
        from ui.app import NetworkTesterApp

        app = NetworkTesterApp()
        screen_manager = app.build()

        # Verify screen manager created
        assert screen_manager is not None

        # Verify screens added
        screen_names = [screen.name for screen in screen_manager.screens]
        assert "menu" in screen_names
        assert "connectivity" in screen_names
        assert "speedtest" in screen_names
        assert "capture" in screen_names

    def test_menu_screen_creation(self):
        """Test menu screen creates properly."""
        from ui.screens.menu import MenuScreen

        screen = MenuScreen(name="test_menu")
        assert screen.name == "test_menu"
        # Screen should have children (UI elements)
        assert len(screen.children) > 0

    def test_connectivity_screen_creation(self):
        """Test connectivity screen creates properly."""
        from ui.screens.connectivity import ConnectivityTestScreen

        screen = ConnectivityTestScreen(name="test_connectivity")
        assert screen.name == "test_connectivity"
        assert screen.test_runner is not None
        assert len(screen.children) > 0

    @patch("testers.connectivity.runner.ConnectivityTestRunner.run_all_tests")
    def test_connectivity_screen_run_tests(self, mock_run_tests):
        """Test connectivity screen can run tests."""
        from testers.connectivity.models import Status, TestResult
        from ui.screens.connectivity import ConnectivityTestScreen

        # Mock test results
        mock_results = {
            "physical_link": TestResult(
                name="Physical Link",
                status=Status.PASSED,
                message="Link up - 1000Mbps Full",
                duration_ms=100,
            )
        }
        mock_run_tests.return_value = mock_results

        screen = ConnectivityTestScreen(name="test")

        # Simulate button press
        mock_button = Mock()
        screen.run_tests(mock_button)

        # Give thread time to start (it's daemon so will be cleaned up)
        import time

        time.sleep(0.1)

        # Test should have started
        assert screen.test_thread is not None

    def test_config_loading(self):
        """Test configuration loading."""
        from utils.config import load_config

        config = load_config()

        # Should have default sections
        assert "logging" in config
        assert "network" in config
        assert "ui" in config

    @patch("ui.screens.menu.logger")
    def test_menu_navigation(self, mock_logger):
        """Test menu screen navigation."""
        from ui.screens.menu import MenuScreen

        screen = MenuScreen(name="menu")

        # Mock screen manager
        screen.manager = Mock()
        screen.manager.current = "menu"

        # Test navigation to connectivity
        mock_button = Mock()
        screen.goto_connectivity(mock_button)

        assert screen.manager.current == "connectivity"
        mock_logger.info.assert_called()


@pytest.mark.system
class TestEndToEndFlow:
    """End-to-end system tests."""

    @patch("testers.connectivity.link.LinkTester.test_link")
    @patch("testers.connectivity.neighbor.NeighborDiscovery.discover_neighbors")
    @patch("testers.connectivity.ip_services.IPServicesTester.test_dhcp")
    @patch("testers.connectivity.ip_services.IPServicesTester.test_dns")
    @patch("testers.connectivity.reachability.ReachabilityTester.ping")
    @patch("testers.connectivity.reachability.ReachabilityTester.get_default_gateway")
    def test_complete_connectivity_workflow(
        self, mock_gateway, mock_ping, mock_dns, mock_dhcp, mock_neighbors, mock_link
    ):
        """Test complete workflow from UI to test execution."""
        from testers.connectivity.models import DHCPResult, DNSResult, LinkStatus, PingResult
        from ui.screens.connectivity import ConnectivityTestScreen

        # Setup mocks for successful test
        mock_link.return_value = LinkStatus(
            interface="eth0", link_up=True, speed_mbps=1000, duplex="Full", carrier=True
        )

        mock_neighbors.return_value = []

        mock_dhcp.return_value = DHCPResult(
            success=True,
            ip_address="192.168.1.100",
            subnet_mask="255.255.255.0",
            gateway="192.168.1.1",
            dns_servers=["8.8.8.8"],
            lease_time=3600,
            message="DHCP active",
        )

        mock_dns.return_value = DNSResult(
            success=True,
            query="google.com",
            resolved_ips=["142.250.185.46"],
            response_time_ms=25.5,
            message="Resolved",
        )

        mock_gateway.return_value = "192.168.1.1"

        mock_ping.return_value = PingResult(
            success=True,
            host="192.168.1.1",
            ip_address="192.168.1.1",
            packets_sent=4,
            packets_received=4,
            packet_loss_percent=0.0,
            min_rtt_ms=1.2,
            avg_rtt_ms=1.5,
            max_rtt_ms=1.8,
            message="Reachable",
        )

        # Create screen and run tests
        screen = ConnectivityTestScreen(name="connectivity")

        # Run tests synchronously for testing
        results = screen.test_runner.run_all_tests()

        # Verify results
        assert len(results) == 6
        assert all(r.name for r in results.values())

        # Display results
        screen._display_results(results)

        # Verify UI was updated (results_labels should be populated)
        assert len(screen.results_labels) > 0
