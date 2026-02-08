"""
Unit tests for link testing module.
"""

from unittest.mock import Mock, mock_open, patch

import pytest
from testers.connectivity.link import LinkTester
from testers.connectivity.models import LinkStatus


@pytest.mark.unit
class TestLinkTester:
    """Test suite for LinkTester class."""

    def test_init(self):
        """Test LinkTester initialization."""
        tester = LinkTester("eth0")
        assert tester.interface == "eth0"

    def test_init_no_interface(self):
        """Test LinkTester initialization without interface."""
        tester = LinkTester()
        assert tester.interface is None

    @patch("subprocess.run")
    def test_get_default_interface_with_default_route(self, mock_run):
        """Test getting default interface from default route."""
        mock_run.return_value = Mock(
            returncode=0, stdout="default via 192.168.1.1 dev eth0 proto dhcp metric 100"
        )

        tester = LinkTester()
        interface = tester.get_default_interface()

        assert interface == "eth0"
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_get_default_interface_fallback(self, mock_run):
        """Test fallback to first non-loopback interface."""
        # First call fails, second succeeds
        mock_run.side_effect = [
            Mock(returncode=1, stdout=""),
            Mock(returncode=0, stdout="1: eth0: <BROADCAST,MULTICAST,UP>\n2: lo: <LOOPBACK>"),
        ]

        tester = LinkTester()
        interface = tester.get_default_interface()

        assert interface == "eth0"

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="1")
    def test_test_link_up(self, mock_file, mock_run):
        """Test link detection when link is up."""
        # Mock ethtool output
        mock_run.side_effect = [
            Mock(returncode=0, stdout="Speed: 1000Mb/s\nDuplex: Full"),
            Mock(returncode=0, stdout="state UP"),
        ]

        tester = LinkTester("eth0")
        status = tester.test_link()

        assert status.interface == "eth0"
        assert status.link_up is True
        assert status.carrier is True
        assert status.speed_mbps == 1000
        assert status.duplex == "Full"

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=mock_open, read_data="0")
    def test_test_link_down(self, mock_file, mock_run):
        """Test link detection when link is down."""
        mock_run.return_value = Mock(returncode=0, stdout="state DOWN")

        tester = LinkTester("eth0")
        status = tester.test_link()

        assert status.interface == "eth0"
        assert status.link_up is False
        assert status.carrier is False

    @patch("subprocess.run")
    def test_check_link_up_true(self, mock_run):
        """Test checking if link is up."""
        mock_run.return_value = Mock(
            returncode=0, stdout="2: eth0: <BROADCAST,MULTICAST,UP> state UP"
        )

        tester = LinkTester("eth0")
        is_up = tester._check_link_up("eth0")

        assert is_up is True

    @patch("subprocess.run")
    def test_check_link_up_false(self, mock_run):
        """Test checking if link is down."""
        mock_run.return_value = Mock(
            returncode=0, stdout="2: eth0: <BROADCAST,MULTICAST> state DOWN"
        )

        tester = LinkTester("eth0")
        is_up = tester._check_link_up("eth0")

        assert is_up is False

    @patch("subprocess.run")
    def test_get_ethtool_info_success(self, mock_run):
        """Test extracting speed and duplex from ethtool."""
        mock_run.return_value = Mock(
            returncode=0, stdout="Speed: 1000Mb/s\nDuplex: Full\nAuto-negotiation: on"
        )

        tester = LinkTester("eth0")
        speed, duplex = tester._get_ethtool_info("eth0")

        assert speed == 1000
        assert duplex == "Full"

    @patch("subprocess.run")
    def test_get_ethtool_info_not_found(self, mock_run):
        """Test when ethtool is not installed."""
        mock_run.side_effect = FileNotFoundError()

        tester = LinkTester("eth0")
        speed, duplex = tester._get_ethtool_info("eth0")

        assert speed is None
        assert duplex is None

    def test_link_status_str(self):
        """Test LinkStatus string representation."""
        status = LinkStatus(
            interface="eth0", link_up=True, speed_mbps=1000, duplex="Full", carrier=True
        )

        assert "eth0" in str(status)
        assert "1000Mbps" in str(status)
        assert "Full" in str(status)

    def test_link_status_str_down(self):
        """Test LinkStatus string representation when down."""
        status = LinkStatus(
            interface="eth0", link_up=False, speed_mbps=None, duplex=None, carrier=False
        )

        assert "Link Down" in str(status)
