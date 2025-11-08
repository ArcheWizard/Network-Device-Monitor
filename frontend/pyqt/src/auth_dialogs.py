"""Authentication dialogs for login and registration."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
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
            logger.exception(f"Login worker error: {e}")
            self.error.emit(str(e))
        finally:
            # Give pending tasks time to complete before closing
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
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
            logger.exception(f"Register worker error: {e}")
            self.error.emit(str(e))
        finally:
            # Give pending tasks time to complete before closing
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _run(self) -> tuple[bool, Optional[str]]:
        return await self.auth_manager.register(
            self.username, self.email, self.password, self.full_name
        )


class LoginDialog(QDialog):
    """Dialog for user login."""

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.worker: Optional[LoginWorker] = None
        self.setWindowTitle("Login")
        self.setModal(True)
        self.resize(350, 200)

        # Form inputs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter username")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password")

        # Form layout
        form_layout = QFormLayout()
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)

        # Buttons
        self.login_btn = QPushButton("Login")
        self.cancel_btn = QPushButton("Cancel")
        self.register_btn = QPushButton("Register New Account")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.login_btn)
        btn_layout.addWidget(self.cancel_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.status_label)
        layout.addLayout(btn_layout)
        layout.addWidget(self.register_btn)
        self.setLayout(layout)

        # Connect signals
        self.login_btn.clicked.connect(self.on_login)
        self.cancel_btn.clicked.connect(self.reject)
        self.register_btn.clicked.connect(self.on_register)
        self.password_input.returnPressed.connect(self.on_login)

    def on_login(self) -> None:
        """Handle login button click."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            self.status_label.setText("Please enter username and password")
            return

        self.status_label.setText("Logging in...")
        self.status_label.setStyleSheet("color: blue;")
        self.login_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.register_btn.setEnabled(False)

        self.worker = LoginWorker(self.auth_manager, username, password)
        self.worker.success.connect(self.on_login_result)
        self.worker.error.connect(self.on_login_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_login_result(self, success: bool) -> None:
        """Handle login result."""
        self.login_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.register_btn.setEnabled(True)

        if success:
            self.status_label.setText("Login successful!")
            self.status_label.setStyleSheet("color: green;")
            self.accept()
        else:
            self.status_label.setText("Login failed: Invalid username or password")
            self.status_label.setStyleSheet("color: red;")

    def on_login_error(self, error_msg: str) -> None:
        """Handle login error."""
        self.login_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.register_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red;")

    def on_register(self) -> None:
        """Open registration dialog."""
        dialog = RegisterDialog(self.auth_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # After successful registration, user can login
            QMessageBox.information(
                self,
                "Registration Successful",
                "Your account has been created. Please login with your credentials.",
            )


class RegisterDialog(QDialog):
    """Dialog for user registration."""

    def __init__(self, auth_manager: AuthManager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.worker: Optional[RegisterWorker] = None
        self.setWindowTitle("Register New Account")
        self.setModal(True)
        self.resize(400, 300)

        # Form inputs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")

        self.full_name_input = QLineEdit()
        self.full_name_input.setPlaceholderText("Full name (optional)")

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Choose a password")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Confirm password")

        # Form layout
        form_layout = QFormLayout()
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Email:", self.email_input)
        form_layout.addRow("Full Name:", self.full_name_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Confirm:", self.confirm_password_input)

        # Password requirements info
        info_label = QLabel(
            "Password must be at least 8 characters long and contain\n"
            "uppercase, lowercase, numbers, and special characters."
        )
        info_label.setStyleSheet("color: gray; font-size: 10px;")

        # Buttons
        self.register_btn = QPushButton("Register")
        self.cancel_btn = QPushButton("Cancel")

        btn_layout = QHBoxLayout()
        btn_layout.addWidget(self.register_btn)
        btn_layout.addWidget(self.cancel_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red;")

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(info_label)
        layout.addWidget(self.status_label)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Connect signals
        self.register_btn.clicked.connect(self.on_register)
        self.cancel_btn.clicked.connect(self.reject)
        self.confirm_password_input.returnPressed.connect(self.on_register)

    def on_register(self) -> None:
        """Handle register button click."""
        username = self.username_input.text().strip()
        email = self.email_input.text().strip()
        full_name = self.full_name_input.text().strip() or None
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Validation
        if not username or not email or not password:
            self.status_label.setText("Please fill in all required fields")
            return

        if password != confirm_password:
            self.status_label.setText("Passwords do not match")
            return

        if len(password) < 8:
            self.status_label.setText("Password must be at least 8 characters")
            return

        self.status_label.setText("Registering...")
        self.status_label.setStyleSheet("color: blue;")
        self.register_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)

        self.worker = RegisterWorker(
            self.auth_manager, username, email, password, full_name
        )
        self.worker.success.connect(self.on_register_result)
        self.worker.error.connect(self.on_register_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def on_register_result(self, success: bool, error_msg: str) -> None:
        """Handle registration result."""
        self.register_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)

        if success:
            self.status_label.setText("Registration successful!")
            self.status_label.setStyleSheet("color: green;")
            self.accept()
        else:
            self.status_label.setText(f"Registration failed: {error_msg}")
            self.status_label.setStyleSheet("color: red;")

    def on_register_error(self, error_msg: str) -> None:
        """Handle registration error."""
        self.register_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("color: red;")
