"""
Main Kivy application for Network Tester.
"""
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from loguru import logger

from ui.screens.capture import CaptureScreen
from ui.screens.connectivity import ConnectivityTestScreen
from ui.screens.menu import MenuScreen
from ui.screens.speedtest import SpeedTestScreen


class NetworkTesterApp(App):
    """Main application class for Network Tester."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = None

    def build(self) -> ScreenManager:
        """Build the application UI."""
        # Configure window for touchscreen
        Window.size = (800, 480)  # 7-inch display typical resolution
        Window.fullscreen = False  # Set to True for production on Pi

        # Create screen manager
        self.screen_manager = ScreenManager()

        # Add screens
        self.screen_manager.add_widget(MenuScreen(name='menu'))
        self.screen_manager.add_widget(ConnectivityTestScreen(name='connectivity'))
        self.screen_manager.add_widget(SpeedTestScreen(name='speedtest'))
        self.screen_manager.add_widget(CaptureScreen(name='capture'))

        logger.info("Application UI initialized")
        return self.screen_manager

    def on_start(self) -> None:
        """Called when application starts."""
        logger.info("Application started")

    def on_stop(self) -> None:
        """Called when application stops."""
        logger.info("Application stopping")
