"""Async API client for the FastAPI backend with WebSocket streaming."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMainWindow, QMenu, QMessageBox, QPushButton, QStatusBar,
                             QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout,
                             QWidget)

try:
    from .api_client import APIClient  # type: ignore[attr-defined]
    from .auth_manager import AuthManager  # type: ignore[attr-defined]
    from .auth_window import AuthWindow  # type: ignore[attr-defined]
    from .device_table_widget import DeviceTableWidget  # type: ignore[attr-defined]
    from .topology_view import TopologyView  # type: ignore[attr-defined]
except ImportError:
    from api_client import APIClient  # type: ignore[no-redef]
    from auth_manager import AuthManager  # type: ignore[no-redef]
    from auth_window import AuthWindow  # type: ignore[no-redef]
    from device_table_widget import DeviceTableWidget  # type: ignore[no-redef]
    from topology_view import TopologyView  # type: ignore[no-redef]

logger = logging.getLogger(__name__)


class FetchDevicesWorker(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(self._run())
            self.result.emit(devices)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _run(self) -> List[Dict[str, Any]]:
        client = APIClient(self.base_url, self.auth_token)
        try:
            return await client.fetch_devices()
        finally:
            await client.aclose()


class TriggerScanWorker(QThread):
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self._run())
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _run(self) -> Dict[str, Any]:
        client = APIClient(self.base_url, self.auth_token)
        try:
            return await client.trigger_scan()
        finally:
            await client.aclose()


class DeleteDeviceWorker(QThread):
    """Worker thread for deleting a device."""

    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, base_url: str, device_id: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.device_id = device_id
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
            self.success.emit()
        except Exception as e:
            logger.error(f"Delete device error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> None:
        client = APIClient(self.base_url, self.auth_token)
        try:
            await client.delete_device(self.device_id)
        finally:
            await client.aclose()


class ArchiveDeviceWorker(QThread):
    """Worker thread for archiving a device."""

    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, base_url: str, device_id: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.device_id = device_id
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
            self.success.emit()
        except Exception as e:
            logger.error(f"Archive device error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> None:
        client = APIClient(self.base_url, self.auth_token)
        try:
            await client.archive_device(self.device_id)
        finally:
            await client.aclose()


class RestoreDeviceWorker(QThread):
    """Worker thread for restoring a device."""

    success = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, base_url: str, device_id: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.device_id = device_id
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
            self.success.emit()
        except Exception as e:
            logger.error(f"Restore device error: {e}")
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> None:
        client = APIClient(self.base_url, self.auth_token)
        try:
            await client.restore_device(self.device_id)
        finally:
            await client.aclose()


class FetchLiveDevicesWorker(QThread):
    """Worker thread for fetching live devices."""

    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(self._run())
            self.result.emit(devices)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> List[Dict[str, Any]]:
        client = APIClient(self.base_url, self.auth_token)
        try:
            return await client.fetch_live_devices()
        finally:
            await client.aclose()


class FetchArchivedDevicesWorker(QThread):
    """Worker thread for fetching archived devices."""

    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.auth_token = auth_token

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            devices = loop.run_until_complete(self._run())
            self.result.emit(devices)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            loop.close()

    async def _run(self) -> List[Dict[str, Any]]:
        client = APIClient(self.base_url, self.auth_token)
        try:
            return await client.fetch_archived_devices()
        finally:
            await client.aclose()


class EventStreamWorker(QThread):
    message = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        super().__init__()
        self.base_url = base_url
        self.auth_token = auth_token
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._run())
        except Exception as e:
            self.error.emit(str(e))
        finally:
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _run(self) -> None:
        client = APIClient(self.base_url, self.auth_token)
        try:
            async for msg in client.stream_events():
                if self._stop:
                    break
                self.message.emit(msg)
        finally:
            await client.aclose()


class AuthCheckWorker(QThread):
    """Worker thread for checking auth requirement and loading saved token."""

    result = pyqtSignal(bool, bool)  # (auth_required, has_valid_token)
    error = pyqtSignal(str)

    def __init__(self, auth_manager: AuthManager):
        super().__init__()
        self.auth_manager = auth_manager

    def run(self) -> None:  # type: ignore[override]
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            auth_required, has_token = loop.run_until_complete(self._run())
            self.result.emit(auth_required, has_token)
        except Exception as e:
            logger.exception(f"Auth check error: {e}")
            self.error.emit(str(e))
        finally:
            pending = asyncio.all_tasks(loop)
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            loop.close()

    async def _run(self) -> tuple[bool, bool]:
        """Check auth requirement and try to load saved token."""
        try:
            auth_required = await self.auth_manager.check_auth_required()

            if auth_required:
                # Try to load saved token
                has_valid_token = await self.auth_manager.load_saved_token()
                return auth_required, has_valid_token
            else:
                return False, False

        except Exception as e:
            logger.exception(f"Error during auth check: {e}")
            raise


class MainWindow(QMainWindow):
    def __init__(self, base_url: str = "http://localhost:8000", auth_manager: Optional[AuthManager] = None):
        super().__init__()
        self.setWindowTitle("Network Device Monitor")
        self.resize(1100, 700)

        self.base_url = base_url

        # Authentication - use provided manager or create new one
        self.auth_manager = auth_manager if auth_manager is not None else AuthManager(base_url)
        self.auth_required = False

        # Top controls
        self.url_input = QLineEdit(self.base_url)
        self.url_input.setPlaceholderText("Backend URL (e.g., http://localhost:8000)")
        self.url_input.setMinimumHeight(36)

        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.setMinimumHeight(36)
        self.refresh_btn.setMinimumWidth(100)

        self.scan_btn = QPushButton("⊕ Scan")
        self.scan_btn.setMinimumHeight(36)
        self.scan_btn.setMinimumWidth(100)

        self.auth_btn = QPushButton("Login")
        self.auth_btn.setProperty("styleClass", "secondary")
        self.auth_btn.setMinimumHeight(36)
        self.auth_btn.setMinimumWidth(100)

        ctl = QWidget()
        ctl_layout = QHBoxLayout()
        ctl_layout.setSpacing(12)
        ctl_layout.setContentsMargins(12, 12, 12, 12)

        backend_label = QLabel("Backend:")
        backend_label.setProperty("styleClass", "muted")
        ctl_layout.addWidget(backend_label)
        ctl_layout.addWidget(self.url_input, 1)
        ctl_layout.addWidget(self.auth_btn)
        ctl_layout.addWidget(self.refresh_btn)
        ctl_layout.addWidget(self.scan_btn)
        ctl.setLayout(ctl_layout)

        # Device tables with filtering
        self.live_devices_table = DeviceTableWidget()
        self.live_devices_table.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.live_devices_table.table.customContextMenuRequested.connect(self.show_live_context_menu)

        self.archived_devices_table = DeviceTableWidget()
        self.archived_devices_table.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.archived_devices_table.table.customContextMenuRequested.connect(self.show_archive_context_menu)
        # Slightly dim archived devices in dark mode
        self.archived_devices_table.table.setStyleSheet("QTableWidget { color: #64748b; }")

        # Topology view tab
        self.topology_view = TopologyView()
        self.topology_view.device_selected.connect(self.on_device_selected)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.live_devices_table, "Live Devices")
        self.tab_widget.addTab(self.archived_devices_table, "Device Archive")
        self.tab_widget.addTab(self.topology_view, "Network Topology")
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Root layout
        root = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(ctl)
        layout.addWidget(self.tab_widget, 1)
        root.setLayout(layout)
        self.setCentralWidget(root)

        # Status bar
        self.status = QStatusBar()
        self.status.showMessage("Ready")
        self.setStatusBar(self.status)

        # Workers
        self.stream_worker: Optional[EventStreamWorker] = None
        self.auth_check_worker: Optional[AuthCheckWorker] = None

        # Signals
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.scan_btn.clicked.connect(self.on_scan)
        self.auth_btn.clicked.connect(self.on_auth_action)

        # Ensure background threads stop on app quit
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.on_app_quit)  # type: ignore[arg-type]

    def showEvent(self, event) -> None:  # type: ignore[override]
        """Handle window show event - perform initial auth check here."""
        super().showEvent(event)
        # Only run once on first show
        if not hasattr(self, "_initial_auth_done"):
            self._initial_auth_done = True
            # If already authenticated (from auth window), skip check and start
            if self.auth_manager.is_authenticated:
                self.auth_required = True
                self.update_auth_ui()
                self.on_refresh()
                self.start_stream()
            else:
                self.check_auth_and_load()

    # ----- Authentication -----
    def check_auth_and_load(self) -> None:
        """Check if auth is required and load saved token if available."""
        # Run auth check in worker thread to avoid blocking Qt event loop
        self.auth_check_worker = AuthCheckWorker(self.auth_manager)
        self.auth_check_worker.result.connect(self._on_auth_check_complete)
        self.auth_check_worker.error.connect(self._on_auth_check_error)
        self.auth_check_worker.finished.connect(self.auth_check_worker.deleteLater)
        self.auth_check_worker.start()

    def _on_auth_check_complete(self, auth_required: bool, has_token: bool) -> None:
        """Handle auth check completion."""
        self.auth_required = auth_required

        if auth_required:
            if has_token:
                # Valid token loaded
                self.update_auth_ui()
                self.on_refresh()
                self.start_stream()
            else:
                # Need to show login dialog
                # Defer to ensure Qt event loop is running
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(100, self.show_login_dialog)
        else:
            # Auth not required
            self.auth_btn.setVisible(False)
            self.on_refresh()
            self.start_stream()

    def _on_auth_check_error(self, error_msg: str) -> None:
        """Handle auth check error."""
        logger.error(f"Auth check error: {error_msg}")
        # Assume auth not required and proceed
        self.auth_btn.setVisible(False)
        self.on_refresh()
        self.start_stream()

    def update_auth_ui(self) -> None:
        """Update UI based on authentication state."""
        if self.auth_manager.is_authenticated:
            user = self.auth_manager.current_user
            if user:
                username = user.get("username", "User")
                role = user.get("role", "")
                self.auth_btn.setText(f"{username} ({role})")
                # Create context menu for logout
                menu = QMenu(self)
                logout_action = menu.addAction("Logout")
                if logout_action:
                    logout_action.triggered.connect(self.on_logout)
                self.auth_btn.setMenu(menu)
        else:
            self.auth_btn.setText("Login")
            self.auth_btn.setMenu(None)

    def show_login_dialog(self) -> None:
        """Show login dialog."""
        dialog = AuthWindow(self.auth_manager, self)
        if dialog.exec() == AuthWindow.DialogCode.Accepted:
            self.update_auth_ui()
            self.on_refresh()
            self.start_stream()
        else:
            # User cancelled login
            if self.auth_required:
                self.status.showMessage("Authentication required to use this application", 0)

    def on_auth_action(self) -> None:
        """Handle auth button click."""
        if self.auth_manager.is_authenticated:
            # Button has menu for logout
            pass
        else:
            self.show_login_dialog()

    def on_logout(self) -> None:
        """Handle logout action."""
        self.auth_manager.logout()
        self.update_auth_ui()
        self.live_devices_table.clear()
        self.archived_devices_table.clear()
        if self.stream_worker:
            self.stream_worker.stop()
            self.stream_worker.wait(1000)
            self.stream_worker = None

        # Close main window and show auth window
        if self.auth_required:
            self.close()  # Close the main window
            # Show auth window with option to close (not mandatory after logout)
            auth_window = AuthWindow(self.auth_manager, allow_close=True)
            result = auth_window.exec()

            if result == AuthWindow.DialogCode.Accepted:
                # User logged back in, create and show new main window
                new_window = MainWindow(self.base_url, self.auth_manager)
                new_window.show()
            # If user closed the window, app will exit naturally

    # ----- UI actions -----
    def on_refresh(self) -> None:
        """Refresh devices in the current tab."""
        self.base_url = self.url_input.text().strip() or self.base_url
        current_tab = self.tab_widget.currentIndex()

        if current_tab == 0:  # Live Devices
            self.refresh_live_devices()
        elif current_tab == 1:  # Archive
            self.refresh_archived_devices()
        elif current_tab == 2:  # Topology
            self.refresh_live_devices()  # Topology uses live devices

    def refresh_live_devices(self) -> None:
        """Refresh live devices list."""
        self.status.showMessage("Fetching live devices…", 2000)
        auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
        worker = FetchLiveDevicesWorker(self.base_url, auth_token)
        worker.setParent(self)
        worker.result.connect(self.on_live_devices_loaded)
        worker.error.connect(lambda e: self.status.showMessage(f"Fetch error: {e}", 5000))
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def refresh_archived_devices(self) -> None:
        """Refresh archived devices list."""
        self.status.showMessage("Fetching archived devices…", 2000)
        auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
        worker = FetchArchivedDevicesWorker(self.base_url, auth_token)
        worker.setParent(self)
        worker.result.connect(self.on_archived_devices_loaded)
        worker.error.connect(lambda e: self.status.showMessage(f"Fetch error: {e}", 5000))
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def on_live_devices_loaded(self, devices: List[Dict[str, Any]]) -> None:
        """Handle live devices data loaded."""
        self.live_devices_table.populate_devices(devices)
        self.topology_view.update_from_devices(devices)
        self.status.showMessage(f"Loaded {len(devices)} live devices", 3000)

    def on_archived_devices_loaded(self, devices: List[Dict[str, Any]]) -> None:
        """Handle archived devices data loaded."""
        self.archived_devices_table.populate_devices(devices)
        self.status.showMessage(f"Loaded {len(devices)} archived devices", 3000)

    def on_tab_changed(self, index: int) -> None:
        """Handle tab change - refresh data for the selected tab."""
        if index == 0:  # Live Devices
            self.refresh_live_devices()
        elif index == 1:  # Archive
            self.refresh_archived_devices()
        # Topology updates from live devices automatically

    def on_scan(self) -> None:
        self.base_url = self.url_input.text().strip() or self.base_url
        self.status.showMessage("Triggering discovery scan…", 2000)
        auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
        worker = TriggerScanWorker(self.base_url, auth_token)
        worker.setParent(self)  # keep strong ref until finished
        worker.done.connect(
            lambda r: self.status.showMessage(
                f"Scan done: {r.get('count', 0)} devices", 5000
            )
        )
        worker.error.connect(
            lambda e: self.status.showMessage(f"Scan error: {e}", 5000)
        )
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def start_stream(self) -> None:
        if self.stream_worker is not None:
            return
        auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
        self.stream_worker = EventStreamWorker(self.base_url, auth_token)
        self.stream_worker.message.connect(self.on_event)
        self.stream_worker.error.connect(
            lambda e: self.status.showMessage(f"WS error: {e}", 5000)
        )
        self.stream_worker.finished.connect(self._clear_stream_worker)
        self.stream_worker.start()

    def _clear_stream_worker(self) -> None:
        self.stream_worker = None

    # ----- Context Menus -----
    def show_live_context_menu(self, position) -> None:  # type: ignore[no-untyped-def]
        """Show context menu for live devices."""
        table = self.live_devices_table.table
        selected_row = table.currentRow()
        if selected_row < 0:
            return

        menu = QMenu(self)

        # Archive action (only if operator+)
        if self.auth_manager.is_operator():
            archive_action = menu.addAction("Archive Device")
            archive_action.triggered.connect(lambda: self.on_archive_device(table))

            # Delete action
            delete_action = menu.addAction("Delete Device (Permanent)")
            delete_action.triggered.connect(lambda: self.on_delete_device(table))

        # Show menu at cursor position
        if menu.actions():
            menu.exec(table.viewport().mapToGlobal(position))

    def show_archive_context_menu(self, position) -> None:  # type: ignore[no-untyped-def]
        """Show context menu for archived devices."""
        table = self.archived_devices_table.table
        selected_row = table.currentRow()
        if selected_row < 0:
            return

        menu = QMenu(self)

        # Restore action (only if operator+)
        if self.auth_manager.is_operator():
            restore_action = menu.addAction("Restore Device")
            restore_action.triggered.connect(lambda: self.on_restore_device(table))

            # Delete action
            delete_action = menu.addAction("Delete Permanently")
            delete_action.triggered.connect(lambda: self.on_delete_device(table))

        # Show menu at cursor position
        if menu.actions():
            menu.exec(table.viewport().mapToGlobal(position))

    def on_archive_device(self, table: QTableWidget) -> None:
        """Handle archive device action."""
        selected_row = table.currentRow()
        if selected_row < 0:
            return

        # Get device info
        device_id_item = table.item(selected_row, 0)
        hostname_item = table.item(selected_row, 3)

        if not device_id_item:
            return

        device_id = device_id_item.text()
        hostname = hostname_item.text() if hostname_item else device_id

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Archive Device",
            f"Archive {hostname}?\n\n"
            f"Archived devices can be restored later.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
            worker = ArchiveDeviceWorker(self.base_url, device_id, auth_token)
            worker.success.connect(lambda: self.on_archive_success(hostname))
            worker.error.connect(self.on_operation_error)
            worker.finished.connect(worker.deleteLater)
            worker.start()
            self.status.showMessage(f"Archiving {hostname}...", 3000)

    def on_restore_device(self, table: QTableWidget) -> None:
        """Handle restore device action."""
        selected_row = table.currentRow()
        if selected_row < 0:
            return

        device_id_item = table.item(selected_row, 0)
        hostname_item = table.item(selected_row, 3)

        if not device_id_item:
            return

        device_id = device_id_item.text()
        hostname = hostname_item.text() if hostname_item else device_id

        auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
        worker = RestoreDeviceWorker(self.base_url, device_id, auth_token)
        worker.success.connect(lambda: self.on_restore_success(hostname))
        worker.error.connect(self.on_operation_error)
        worker.finished.connect(worker.deleteLater)
        worker.start()
        self.status.showMessage(f"Restoring {hostname}...", 3000)

    def on_delete_device(self, table: QTableWidget) -> None:
        """Handle delete device action."""
        selected_row = table.currentRow()
        if selected_row < 0:
            return

        # Get device info
        device_id_item = table.item(selected_row, 0)
        hostname_item = table.item(selected_row, 3)
        ip_item = table.item(selected_row, 1)

        if not device_id_item:
            return

        device_id = device_id_item.text()
        hostname = hostname_item.text() if hostname_item else device_id
        ip = ip_item.text() if ip_item else ""

        # Confirmation dialog
        reply = QMessageBox.warning(
            self,
            "Delete Device Permanently",
            f"Permanently delete {hostname}?\n\n"
            f"IP: {ip}\n"
            f"ID: {device_id}\n\n"
            f"This action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            auth_token = self.auth_manager._token if self.auth_manager.is_authenticated else None
            worker = DeleteDeviceWorker(self.base_url, device_id, auth_token)
            worker.success.connect(lambda: self.on_delete_success(hostname))
            worker.error.connect(self.on_operation_error)
            worker.finished.connect(worker.deleteLater)
            worker.start()
            self.status.showMessage(f"Deleting {hostname}...", 3000)

    def on_archive_success(self, hostname: str) -> None:
        """Handle successful device archival."""
        self.status.showMessage(f"Archived {hostname}", 3000)
        self.refresh_live_devices()

    def on_restore_success(self, hostname: str) -> None:
        """Handle successful device restoration."""
        self.status.showMessage(f"Restored {hostname}", 3000)
        self.refresh_archived_devices()
        self.refresh_live_devices()

    def on_delete_success(self, hostname: str) -> None:
        """Handle successful device deletion."""
        self.status.showMessage(f"Deleted {hostname}", 3000)
        self.on_refresh()

    def on_operation_error(self, error_msg: str) -> None:
        """Handle device operation error."""
        QMessageBox.critical(
            self,
            "Operation Failed",
            f"Failed to perform operation:\n\n{error_msg}"
        )
        self.status.showMessage("Operation failed", 3000)

    # ----- WebSocket Events -----
    def on_event(self, msg: Dict[str, Any]) -> None:
        """Handle WebSocket events - update live devices only."""
        mtype = msg.get("type")

        # On discovery complete or device updates, refresh live devices
        if mtype in ("device_discovered", "device_up", "device_down", "scan_complete"):
            # Only refresh if we're on the live devices tab
            if self.tab_widget.currentIndex() == 0:
                self.refresh_live_devices()

        # Show status message
        if mtype == "device_discovered":
            device = msg.get("device", {})
            hostname = device.get("hostname") or device.get("ip") or "Unknown"
            self.status.showMessage(f"Discovered: {hostname}", 2000)
        elif mtype in ("device_up", "device_down"):
            device_id = msg.get("device_id", "Unknown")
            status = "up" if mtype == "device_up" else "down"
            self.status.showMessage(f"Device {device_id} is {status}", 2000)

    def on_device_selected(self, device_id: str) -> None:
        """Handle device selection from topology view."""
        # Switch to live devices tab
        self.tab_widget.setCurrentIndex(0)
        # Note: Could enhance this to find and select the device in the table

    # ----- lifecycle -----
    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.stream_worker is not None:
            self.stream_worker.stop()
            self.stream_worker.wait(1000)
            self.stream_worker = None
        # Clean up auth manager
        asyncio.run(self.auth_manager.aclose())
        super().closeEvent(event)

    def on_app_quit(self) -> None:
        # Gracefully stop workers when the app is quitting
        if self.stream_worker is not None:
            self.stream_worker.stop()
            self.stream_worker.wait(500)
        # Clean up auth manager
        asyncio.run(self.auth_manager.aclose())
