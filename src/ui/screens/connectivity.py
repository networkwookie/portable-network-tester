"""
Connectivity test screen for Network Tester.
"""
import threading

from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from loguru import logger

from testers.connectivity.models import Status, TestResult
from testers.connectivity.runner import ConnectivityTestRunner


class ConnectivityTestScreen(Screen):
    """Screen for running connectivity tests."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.test_runner = ConnectivityTestRunner()
        self.test_thread = None
        self.results_labels = {}
        self.build_ui()

    def build_ui(self) -> None:
        """Build the connectivity test UI."""
        # Main layout
        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        # Add background
        with layout.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)

        layout.bind(size=self._update_rect, pos=self._update_rect)

        # Header with back button
        header = BoxLayout(size_hint=(1, 0.1), spacing=10)

        btn_back = Button(
            text="← Back", size_hint=(0.2, 1), background_color=(0.3, 0.3, 0.3, 1), font_size="18sp"
        )
        btn_back.bind(on_press=self.go_back)
        header.add_widget(btn_back)

        title = Label(
            text="[b]Connectivity Test[/b]",
            markup=True,
            font_size="28sp",
            size_hint=(0.6, 1),
            color=(0.2, 0.8, 1, 1),
        )
        header.add_widget(title)

        btn_run = Button(
            text="Run Tests",
            size_hint=(0.2, 1),
            background_color=(0.2, 0.7, 0.3, 1),
            font_size="18sp",
        )
        btn_run.bind(on_press=self.run_tests)
        header.add_widget(btn_run)

        layout.add_widget(header)

        # Progress bar
        self.progress_bar = ProgressBar(max=100, size_hint=(1, 0.05))
        layout.add_widget(self.progress_bar)

        # Results area (scrollable)
        scroll_view = ScrollView(size_hint=(1, 0.85))
        self.results_layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
        self.results_layout.bind(minimum_height=self.results_layout.setter("height"))

        # Create result placeholders
        self._create_result_display("Physical Link", "link")
        self._create_result_display("Neighbor Discovery (LLDP)", "neighbor")
        self._create_result_display("DHCP Service", "dhcp")
        self._create_result_display("DNS Service", "dns")
        self._create_result_display("Gateway Reachability", "gateway")
        self._create_result_display("Internet Reachability", "internet")

        scroll_view.add_widget(self.results_layout)
        layout.add_widget(scroll_view)

        self.add_widget(layout)

    def _create_result_display(self, test_name: str, test_key: str) -> None:
        """Create a result display widget for a test."""
        container = BoxLayout(orientation="vertical", size_hint_y=None, height=120, spacing=5)

        # Test header
        header_box = BoxLayout(size_hint=(1, 0.3))
        name_label = Label(
            text=f"[b]{test_name}[/b]",
            markup=True,
            font_size="18sp",
            size_hint=(0.7, 1),
            halign="left",
            valign="middle",
        )
        name_label.bind(size=name_label.setter("text_size"))
        header_box.add_widget(name_label)

        status_label = Label(
            text="[color=#808080]Pending[/color]",
            markup=True,
            font_size="16sp",
            size_hint=(0.3, 1),
            halign="right",
            valign="middle",
        )
        status_label.bind(size=status_label.setter("text_size"))
        header_box.add_widget(status_label)

        container.add_widget(header_box)

        # Details label
        details_label = Label(
            text="",
            font_size="14sp",
            size_hint=(1, 0.7),
            halign="left",
            valign="top",
            color=(0.8, 0.8, 0.8, 1),
        )
        details_label.bind(size=details_label.setter("text_size"))
        container.add_widget(details_label)

        # Store references
        self.results_labels[test_key] = {
            "container": container,
            "status": status_label,
            "details": details_label,
        }

        self.results_layout.add_widget(container)

    def _update_rect(self, instance, value) -> None:
        """Update background rectangle."""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def go_back(self, instance) -> None:
        """Navigate back to menu."""
        logger.info("Returning to menu")
        self.manager.current = "menu"

    def run_tests(self, instance) -> None:
        """Run connectivity tests in background thread."""
        if self.test_thread and self.test_thread.is_alive():
            logger.warning("Tests already running")
            return

        logger.info("Starting connectivity tests")
        self.progress_bar.value = 0

        # Reset all results
        for key in self.results_labels:
            self._update_test_result(key, Status.PENDING, "")

        # Run tests in background
        self.test_thread = threading.Thread(target=self._run_tests_thread, daemon=True)
        self.test_thread.start()

    def _run_tests_thread(self) -> None:
        """Background thread for running tests."""
        try:
            results = self.test_runner.run_all_tests(progress_callback=self._update_progress)
            Clock.schedule_once(lambda dt: self._display_results(results))
        except Exception as e:
            logger.exception(f"Error running tests: {e}")
            Clock.schedule_once(lambda dt: self._show_error(str(e)))

    def _update_progress(self, progress: float) -> None:
        """Update progress bar."""
        Clock.schedule_once(lambda dt: setattr(self.progress_bar, "value", progress * 100))

    def _display_results(self, results: dict[str, TestResult]) -> None:
        """Display test results."""
        test_mapping = {
            "link": "physical_link",
            "neighbor": "neighbor_discovery",
            "dhcp": "dhcp",
            "dns": "dns",
            "gateway": "gateway_ping",
            "internet": "internet_ping",
        }

        for ui_key, result_key in test_mapping.items():
            if result_key in results:
                result = results[result_key]
                self._update_test_result(ui_key, result.status, result.message)

    def _update_test_result(self, test_key: str, status: Status, message: str) -> None:
        """Update a test result display."""
        if test_key not in self.results_labels:
            return

        labels = self.results_labels[test_key]

        # Update status with color
        status_colors = {
            Status.PASSED: "#00ff00",
            Status.FAILED: "#ff0000",
            Status.WARNING: "#ffaa00",
            Status.PENDING: "#808080",
            Status.RUNNING: "#00aaff",
        }

        color = status_colors.get(status, "#808080")
        labels["status"].text = f"[color={color}]{status.value}[/color]"

        # Update details
        labels["details"].text = message

    def _show_error(self, error: str) -> None:
        """Show error message."""
        logger.error(f"Test error: {error}")
        # Could add error popup here
