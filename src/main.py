"""
Main entry point for Portable Network Tester application.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from ui.app import NetworkTesterApp
from utils.config import load_config


def setup_logging() -> None:
    """Configure logging for the application."""
    config = load_config()
    log_level = config.get("logging", {}).get("level", "INFO")
    log_path = config.get("logging", {}).get("path", "logs/network_tester.log")

    # Remove default logger
    logger.remove()

    # Add console handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=log_level,
        colorize=True,
    )

    # Add file handler
    logger.add(
        log_path,
        rotation="10 MB",
        retention="1 week",
        compression="zip",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )


def main() -> int:
    """Run the main application."""
    try:
        setup_logging()
        logger.info("Starting Portable Network Tester")

        app = NetworkTesterApp()
        app.run()

        logger.info("Application closed normally")
        return 0

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
