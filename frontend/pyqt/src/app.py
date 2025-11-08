"""Network Device Monitor PyQt6 Application Entry Point."""

import asyncio
import logging
import sys

from auth_manager import AuthManager
from auth_window import AuthWindow
from main_window import MainWindow
from PyQt6.QtWidgets import QApplication, QDialog
from styles import get_stylesheet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Main application entry point."""
    app = QApplication(sys.argv)

    # Apply global stylesheet for professional appearance
    app.setStyleSheet(get_stylesheet())

    # Configuration
    base_url = "http://localhost:8000"

    # Initialize auth manager
    auth_manager = AuthManager(base_url)

    # Check if authentication is required
    try:
        auth_required = asyncio.run(auth_manager.check_auth_required())
        logger.info(f"Authentication required: {auth_required}")
    except Exception as e:
        logger.error(f"Failed to check auth requirements: {e}")
        auth_required = False

    # If auth is required, try to load saved token or show auth window
    if auth_required:
        has_token = asyncio.run(auth_manager.load_saved_token())
        logger.info(f"Has saved token: {has_token}")

        if not has_token:
            # Show mandatory auth window
            logger.info("Showing authentication window")
            auth_window = AuthWindow(auth_manager)
            result = auth_window.exec()

            if result != QDialog.DialogCode.Accepted:
                # User somehow closed window - exit app
                logger.warning("Authentication window closed without success")
                return 1

            logger.info(f"User authenticated as: {auth_manager.current_user}")

    # Now show main window with authenticated user
    window = MainWindow(base_url, auth_manager)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
