"""Mandatory authentication window shown before main application."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

try:
    from .auth_manager import AuthManager  # type: ignore[attr-defined]
except ImportError:
    from auth_manager import AuthManager  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


class LoginWorker(QThread):
    """Worker thread for async login operation."""

    success = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, auth_manager: AuthManager, username: str, password: str):
        super().__init__()
        self.auth_manager = auth_manager
        self.username = username
        self.password = password

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._run())
            self.success.emit(result)
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> bool:
        return await self.auth_manager.login(self.username, self.password)


class RegisterWorker(QThread):
    """Worker thread for async registration operation."""

    success = pyqtSignal(bool, str)  # (success, error_message)
    error = pyqtSignal(str)

    def __init__(
        self,
        auth_manager: AuthManager,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ):
        super().__init__()
        self.auth_manager = auth_manager
        self.username = username
        self.email = email
        self.password = password
        self.full_name = full_name

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result, error_msg = loop.run_until_complete(self._run())
            self.success.emit(result, error_msg or "")
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> tuple[bool, Optional[str]]:
        return await self.auth_manager.register(
            self.username, self.email, self.password, self.full_name
        )


class LoginTab(QWidget):
    """Login tab widget."""

    login_successful = pyqtSignal()

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.worker: Optional[LoginWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Login to Network Device Monitor")
        header.setProperty("styleClass", "heading")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 10, 0, 10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.username_input.setMinimumHeight(36)
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")
        self.password_input.setMinimumHeight(36)
        self.password_input.returnPressed.connect(self.on_login)
        form_layout.addRow("Password:", self.password_input)

        layout.addLayout(form_layout)

        # Status label
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(24)
        layout.addWidget(self.status_label)

        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.on_login)
        self.login_btn.setDefault(True)
        self.login_btn.setMinimumHeight(40)
        layout.addWidget(self.login_btn)

        layout.addStretch()
        self.setLayout(layout)

    def on_login(self) -> None:
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.status_label.setText("⚠ Please enter username and password")
            self.status_label.setStyleSheet("color: #f59e0b;")  # Warning color
            return

        # Disable inputs during login
        self.login_btn.setEnabled(False)
        self.username_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.status_label.setText("🔄 Logging in...")
        self.status_label.setStyleSheet("color: #3b82f6;")  # Info color

        # Start login worker
        self.worker = LoginWorker(self.auth_manager, username, password)
        self.worker.success.connect(self.on_login_result)
        self.worker.error.connect(self.on_login_error)
        self.worker.start()

    def on_login_result(self, success: bool) -> None:
        """Handle login result."""
        self.login_btn.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)

        if success:
            self.status_label.setText("✓ Login successful!")
            self.status_label.setStyleSheet("color: #10b981;")  # Success color
            self.login_successful.emit()
        else:
            self.status_label.setText("✗ Login failed. Please check your credentials.")
            self.status_label.setStyleSheet("color: #ef4444;")  # Error color

    def on_login_error(self, error_msg: str) -> None:
        """Handle login error."""
        self.login_btn.setEnabled(True)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("QLabel { color: red; }")


class RegisterTab(QWidget):
    """Registration tab widget."""

    register_successful = pyqtSignal()

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.worker: Optional[RegisterWorker] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Create Your Account")
        header.setProperty("styleClass", "heading")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 10, 0, 10)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("3-50 alphanumeric characters")
        self.username_input.setMinimumHeight(36)
        form_layout.addRow("Username:", self.username_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        self.email_input.setMinimumHeight(36)
        form_layout.addRow("Email:", self.email_input)

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Optional")
        self.full_name_input.setMinimumHeight(36)
        form_layout.addRow("Full Name:", self.full_name_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Min 8 chars, 1 uppercase, 1 digit")
        self.password_input.setMinimumHeight(36)
        form_layout.addRow("Password:", self.password_input)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Re-enter password")
        self.confirm_password_input.setMinimumHeight(36)
        self.confirm_password_input.returnPressed.connect(self.on_register)
        form_layout.addRow("Confirm:", self.confirm_password_input)

        layout.addLayout(form_layout)

        # Status label
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setMinimumHeight(24)
        layout.addWidget(self.status_label)

        # Register button
        self.register_btn = QPushButton("Register")
        self.register_btn.clicked.connect(self.on_register)
        self.register_btn.setMinimumHeight(40)
        layout.addWidget(self.register_btn)

        layout.addStretch()
        self.setLayout(layout)

    def on_register(self) -> None:
        """Handle register button click."""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        full_name = self.full_name_input.text().strip() or None
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validation
        if not username or not email or not password:
            self.status_label.setText("⚠ Please fill in all required fields")
            self.status_label.setStyleSheet("color: #f59e0b;")
            return

        if password != confirm_password:
            self.status_label.setText("⚠ Passwords do not match")
            self.status_label.setStyleSheet("color: #f59e0b;")
            return

        # Disable inputs during registration
        self.register_btn.setEnabled(False)
        self.username_input.setEnabled(False)
        self.email_input.setEnabled(False)
        self.full_name_input.setEnabled(False)
        self.password_input.setEnabled(False)
        self.confirm_password_input.setEnabled(False)
        self.status_label.setText("🔄 Registering...")
        self.status_label.setStyleSheet("color: #3b82f6;")

        # Start registration worker
        self.worker = RegisterWorker(
            self.auth_manager, username, email, password, full_name
        )
        self.worker.success.connect(self.on_register_result)
        self.worker.error.connect(self.on_register_error)
        self.worker.start()

    def on_register_result(self, success: bool, error_msg: str) -> None:
        """Handle registration result."""
        self.register_btn.setEnabled(True)
        self.username_input.setEnabled(True)
        self.email_input.setEnabled(True)
        self.full_name_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.confirm_password_input.setEnabled(True)

        if success:
            self.status_label.setText(
                "✓ Registration successful! Please switch to Login tab."
            )
            self.status_label.setStyleSheet("color: #10b981;")
            self.register_successful.emit()
        else:
            self.status_label.setText(f"✗ Registration failed: {error_msg}")
            self.status_label.setStyleSheet("color: #ef4444;")

    def on_register_error(self, error_msg: str) -> None:
        """Handle registration error."""
        self.register_btn.setEnabled(True)
        self.username_input.setEnabled(True)
        self.email_input.setEnabled(True)
        self.full_name_input.setEnabled(True)
        self.password_input.setEnabled(True)
        self.confirm_password_input.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("QLabel { color: red; }")


class AuthWindow(QDialog):
    """Standalone authentication window shown before main application.

    This window is modal and can optionally be closed if allow_close=True.
    When shown at startup, it's mandatory (allow_close=False).
    When shown after logout, it's optional (allow_close=True).
    """

    def __init__(self, auth_manager: AuthManager, parent=None, allow_close: bool = False):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.allow_close = allow_close
        self.setModal(True)
        self.setWindowTitle("Network Device Monitor - Authentication Required")
        self.setMinimumWidth(480)
        self.setMinimumHeight(500)

        # Only disable close button if not allowed to close
        if not allow_close:
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Network Device Monitor")
        header.setProperty("styleClass", "heading")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(header)

        info = QLabel(
            "Please log in to access the application. If you don't have an account, "
            "use the Register tab to create one."
        )
        info.setProperty("styleClass", "muted")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setWordWrap(True)
        layout.addWidget(info)

        layout.addSpacing(12)

        # Tab widget with Login and Register tabs
        self.tabs = QTabWidget()
        self.login_tab = LoginTab(self.auth_manager)
        self.register_tab = RegisterTab(self.auth_manager)

        self.tabs.addTab(self.login_tab, "Login")
        self.tabs.addTab(self.register_tab, "Register")

        layout.addWidget(self.tabs)

        # Connect signals
        self.login_tab.login_successful.connect(self.on_auth_success)
        self.register_tab.register_successful.connect(self.on_register_success)

        self.setLayout(layout)

    def on_auth_success(self) -> None:
        """Handle successful authentication."""
        logger.info("Authentication successful")
        self.accept()

    def on_register_success(self) -> None:
        """Handle successful registration - switch to login tab."""
        logger.info("Registration successful, switching to login tab")
        self.tabs.setCurrentIndex(0)  # Switch to login tab

    def closeEvent(self, event) -> None:  # type: ignore[override]
        """Handle window close event - allow or prevent based on allow_close flag."""
        if self.allow_close:
            # Allow closing after logout
            event.accept()
        else:
            # Prevent closing at startup - user must authenticate
            event.ignore()
            QMessageBox.warning(
                self,
                "Authentication Required",
                "You must log in to use the application.\n\n"
                "If you want to exit, please close the application from your system.",
            )

    def reject(self) -> None:
        """Override reject to handle Escape key based on allow_close flag."""
        if self.allow_close:
            # Allow closing with Escape after logout
            super().reject()
        # Otherwise do nothing - user must authenticate
