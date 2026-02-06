"""
Main menu screen for Network Tester.
"""
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from loguru import logger


class MenuScreen(Screen):
    """Main menu screen with test options."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self) -> None:
        """Build the menu UI."""
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Add background
        with layout.canvas.before:
            Color(0.1, 0.1, 0.15, 1)
            self.rect = Rectangle(size=layout.size, pos=layout.pos)

        layout.bind(size=self._update_rect, pos=self._update_rect)

        # Title
        title = Label(
            text='[b]Portable Network Tester[/b]',
            markup=True,
            font_size='32sp',
            size_hint=(1, 0.2),
            color=(0.2, 0.8, 1, 1)
        )
        layout.add_widget(title)

        # Test buttons
        btn_connectivity = self._create_menu_button(
            'Connectivity Test',
            'Test physical link, neighbor discovery, DHCP, DNS, and reachability',
            self.goto_connectivity
        )
        layout.add_widget(btn_connectivity)

        btn_speedtest = self._create_menu_button(
            'Speed Test',
            'Measure network bandwidth and latency',
            self.goto_speedtest
        )
        layout.add_widget(btn_speedtest)

        btn_capture = self._create_menu_button(
            'Packet Capture',
            'Capture and analyze network traffic',
            self.goto_capture
        )
        layout.add_widget(btn_capture)

        # Exit button
        btn_exit = Button(
            text='Exit',
            size_hint=(1, 0.15),
            background_color=(0.8, 0.2, 0.2, 1),
            font_size='20sp'
        )
        btn_exit.bind(on_press=self.exit_app)
        layout.add_widget(btn_exit)

        self.add_widget(layout)

    def _create_menu_button(self, title: str, description: str, callback) -> BoxLayout:
        """Create a styled menu button with title and description."""
        container = BoxLayout(orientation='vertical', size_hint=(1, 0.25), spacing=5)

        btn = Button(
            text=f'[b]{title}[/b]\n[size=14sp]{description}[/size]',
            markup=True,
            background_color=(0.2, 0.5, 0.8, 1),
            font_size='22sp',
        )
        btn.bind(on_press=callback)

        container.add_widget(btn)
        return container

    def _update_rect(self, instance, value) -> None:
        """Update background rectangle."""
        self.rect.pos = instance.pos
        self.rect.size = instance.size

    def goto_connectivity(self, instance) -> None:
        """Navigate to connectivity test screen."""
        logger.info("Navigating to Connectivity Test")
        self.manager.current = 'connectivity'

    def goto_speedtest(self, instance) -> None:
        """Navigate to speed test screen."""
        logger.info("Navigating to Speed Test")
        self.manager.current = 'speedtest'

    def goto_capture(self, instance) -> None:
        """Navigate to packet capture screen."""
        logger.info("Navigating to Packet Capture")
        self.manager.current = 'capture'

    def exit_app(self, instance) -> None:
        """Exit the application."""
        logger.info("User requested exit")
        from kivy.app import App
        App.get_running_app().stop()
