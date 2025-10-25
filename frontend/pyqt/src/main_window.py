from __future__ import annotations

from typing import Any, Dict, List, Optional
import asyncio

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLineEdit,
    QStatusBar,
)

try:
    from .api_client import APIClient  # type: ignore[attr-defined]
except ImportError:
    from api_client import APIClient  # type: ignore[no-redef]


class FetchDevicesWorker(QThread):
    result = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url

    def run(self) -> None:  # type: ignore[override]
        try:
            devices = asyncio.run(self._run())
            self.result.emit(devices)
        except Exception as e:
            self.error.emit(str(e))

    async def _run(self) -> List[Dict[str, Any]]:
        client = APIClient(self.base_url)
        try:
            return await client.fetch_devices()
        finally:
            await client.aclose()


class TriggerScanWorker(QThread):
    done = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url

    def run(self) -> None:  # type: ignore[override]
        try:
            result = asyncio.run(self._run())
            self.done.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    async def _run(self) -> Dict[str, Any]:
        client = APIClient(self.base_url)
        try:
            return await client.trigger_scan()
        finally:
            await client.aclose()


class EventStreamWorker(QThread):
    message = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self._stop = False

    def stop(self) -> None:
        self._stop = True

    def run(self) -> None:  # type: ignore[override]
        try:
            asyncio.run(self._run())
        except Exception as e:
            self.error.emit(str(e))

    async def _run(self) -> None:
        client = APIClient(self.base_url)
        try:
            async for msg in client.stream_events():
                if self._stop:
                    break
                self.message.emit(msg)
        finally:
            await client.aclose()


class MainWindow(QMainWindow):
    COLS = [
        "ID",
        "IP",
        "MAC",
        "Hostname",
        "Vendor",
        "Status",
        "Latency(ms)",
        "Loss",
    ]

    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__()
        self.setWindowTitle("Network Device Monitor")
        self.resize(900, 600)

        self.base_url = base_url
        self._rows_by_id: dict[str, int] = {}

        # Top controls
        self.url_input = QLineEdit(self.base_url)
        self.url_input.setPlaceholderText("Backend URL (e.g., http://localhost:8000)")
        self.refresh_btn = QPushButton("Refresh")
        self.scan_btn = QPushButton("Scan")

        ctl = QWidget()
        ctl_layout = QHBoxLayout()
        ctl_layout.addWidget(QLabel("Backend:"))
        ctl_layout.addWidget(self.url_input, 1)
        ctl_layout.addWidget(self.refresh_btn)
        ctl_layout.addWidget(self.scan_btn)
        ctl.setLayout(ctl_layout)

        # Device table
        self.table = QTableWidget(0, len(self.COLS))
        self.table.setHorizontalHeaderLabels(self.COLS)
        header = self.table.horizontalHeader()
        assert isinstance(header, QHeaderView)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)

        # Root layout
        root = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(ctl)
        layout.addWidget(self.table, 1)
        root.setLayout(layout)
        self.setCentralWidget(root)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Workers
        self.stream_worker: Optional[EventStreamWorker] = None

        # Signals
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.scan_btn.clicked.connect(self.on_scan)

        # Initial actions
        self.on_refresh()
        self.start_stream()

        # Ensure background threads stop on app quit
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.on_app_quit)  # type: ignore[arg-type]

    # ----- UI actions -----
    def on_refresh(self) -> None:
        self.base_url = self.url_input.text().strip() or self.base_url
        self.status.showMessage("Fetching devices…", 2000)
        worker = FetchDevicesWorker(self.base_url)
        worker.setParent(self)  # keep strong ref until finished
        worker.result.connect(self.populate_devices)
        worker.error.connect(
            lambda e: self.status.showMessage(f"Fetch error: {e}", 5000)
        )
        # Keep reference until finished
        worker.finished.connect(worker.deleteLater)
        worker.start()

    def on_scan(self) -> None:
        self.base_url = self.url_input.text().strip() or self.base_url
        self.status.showMessage("Triggering discovery scan…", 2000)
        worker = TriggerScanWorker(self.base_url)
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
        self.stream_worker = EventStreamWorker(self.base_url)
        self.stream_worker.message.connect(self.on_event)
        self.stream_worker.error.connect(
            lambda e: self.status.showMessage(f"WS error: {e}", 5000)
        )
        self.stream_worker.finished.connect(self._clear_stream_worker)
        self.stream_worker.start()

    def _clear_stream_worker(self) -> None:
        self.stream_worker = None

    # ----- Data binding -----
    def populate_devices(self, devices: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(0)
        self._rows_by_id.clear()
        for dev in devices:
            self.upsert_device_row(dev)
        self.status.showMessage(f"Loaded {len(devices)} devices", 3000)

    def upsert_device_row(self, dev: Dict[str, Any]) -> None:
        dev_id = str(dev.get("id") or dev.get("mac") or dev.get("ip") or "")
        if not dev_id:
            return
        row = self._rows_by_id.get(dev_id)
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self._rows_by_id[dev_id] = row
        values = [
            dev_id,
            str(dev.get("ip") or ""),
            str(dev.get("mac") or ""),
            str(dev.get("hostname") or ""),
            str(dev.get("vendor") or ""),
            str(dev.get("status") or "unknown"),
            "",
            "",
        ]
        for col, val in enumerate(values):
            self.table.setItem(row, col, QTableWidgetItem(val))

    def on_event(self, msg: Dict[str, Any]) -> None:
        mtype = msg.get("type")
        dev_id = str(msg.get("device_id") or "")
        if not dev_id:
            # device_discovered event carries a 'device' object instead
            if mtype == "device_discovered" and isinstance(msg.get("device"), dict):
                self.upsert_device_row(msg["device"])
            return
        row = self._rows_by_id.get(dev_id)
        if row is None:
            # Create minimal row if unknown
            self.upsert_device_row(
                {"id": dev_id, "ip": msg.get("ip", ""), "status": "unknown"}
            )
            row = self._rows_by_id.get(dev_id)
        if row is None:
            return
        if mtype in ("device_up", "device_down"):
            status_text = "up" if mtype == "device_up" else "down"
            self.table.setItem(row, 5, QTableWidgetItem(status_text))
            self.status.showMessage(f"Device {dev_id} is {status_text}", 3000)
        elif mtype == "latency":
            ms = msg.get("ms") or msg.get("latency_avg")
            loss = msg.get("loss") or msg.get("packet_loss")
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(f"{ms:.1f}" if isinstance(ms, (int, float)) else ""),
            )
            self.table.setItem(
                row,
                7,
                QTableWidgetItem(
                    f"{loss:.2f}" if isinstance(loss, (int, float)) else ""
                ),
            )

    # ----- lifecycle -----
    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self.stream_worker is not None:
            self.stream_worker.stop()
            self.stream_worker.wait(1000)
            self.stream_worker = None
        super().closeEvent(event)

    def on_app_quit(self) -> None:
        # Gracefully stop workers when the app is quitting
        if self.stream_worker is not None:
            self.stream_worker.stop()
            self.stream_worker.wait(500)
