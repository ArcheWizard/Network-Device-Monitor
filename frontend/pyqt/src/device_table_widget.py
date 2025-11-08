"""Enhanced device table widget with filtering and sorting."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class DeviceTableWidget(QWidget):
    """Enhanced table widget with filtering and sorting capabilities."""

    COLUMNS = [
        "ID",
        "IP",
        "MAC",
        "Hostname",
        "Vendor",
        "Status",
        "Latency(ms)",
        "Loss",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._devices: List[Dict[str, Any]] = []

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Filter controls
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(8)

        filter_label = QLabel("Filter by:")
        filter_label.setProperty("styleClass", "muted")
        filter_layout.addWidget(filter_label)

        self.filter_column = QComboBox()
        self.filter_column.addItems(["All"] + self.COLUMNS)
        self.filter_column.setMinimumWidth(150)
        filter_layout.addWidget(self.filter_column)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Type to filter devices...")
        self.filter_input.textChanged.connect(self.apply_filter)
        self.filter_input.setMinimumHeight(32)
        filter_layout.addWidget(self.filter_input, 1)

        self.clear_filter_btn = QPushButton("Clear")
        self.clear_filter_btn.setProperty("styleClass", "secondary")
        self.clear_filter_btn.clicked.connect(self.clear_filter)
        self.clear_filter_btn.setMinimumHeight(32)
        filter_layout.addWidget(self.clear_filter_btn)

        layout.addLayout(filter_layout)

        # Table with sorting enabled
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        header = self.table.horizontalHeader()
        assert isinstance(header, QHeaderView)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(False)

        # Configure vertical header (row numbers)
        vertical_header = self.table.verticalHeader()
        assert isinstance(vertical_header, QHeaderView)
        # Set default section resize mode for auto-height adjustment
        vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        # Set minimum section size for better readability
        vertical_header.setMinimumSectionSize(36)
        # Ensure vertical header uses same styling as global stylesheet
        # Remove any custom styling to rely on global styles from styles.py

        layout.addWidget(self.table)

        self.setLayout(layout)

    def apply_filter(self, text: str = "") -> None:
        """Filter table rows based on input text."""
        if not text:
            text = self.filter_input.text()

        text = text.lower()
        column = self.filter_column.currentText()

        for row in range(self.table.rowCount()):
            should_show = False

            if column == "All":
                # Search across all columns
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and text in item.text().lower():
                        should_show = True
                        break
            else:
                # Search specific column
                col_index = self.get_column_index(column)
                if col_index >= 0:
                    item = self.table.item(row, col_index)
                    if item and text in item.text().lower():
                        should_show = True

            self.table.setRowHidden(row, not should_show)

    def clear_filter(self) -> None:
        """Clear the filter and show all rows."""
        self.filter_input.clear()
        for row in range(self.table.rowCount()):
            self.table.setRowHidden(row, False)

    def get_column_index(self, column_name: str) -> int:
        """Get the index of a column by name."""
        try:
            return self.COLUMNS.index(column_name)
        except ValueError:
            return -1

    def populate_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Populate the table with device data."""
        # Temporarily disable sorting for faster population
        self.table.setSortingEnabled(False)

        self.table.setRowCount(0)
        self._devices = devices

        for dev in devices:
            self.add_device_row(dev)

        # Re-enable sorting
        self.table.setSortingEnabled(True)

        # Reapply filter if active
        if self.filter_input.text():
            self.apply_filter()

    def add_device_row(self, dev: Dict[str, Any]) -> None:
        """Add a single device row to the table."""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # ID
        dev_id = dev.get("mac") or dev.get("id") or dev.get("ip") or ""
        self.table.setItem(row, 0, QTableWidgetItem(str(dev_id)))

        # IP
        ip = dev.get("ip", "")
        self.table.setItem(row, 1, QTableWidgetItem(str(ip)))

        # MAC
        mac = dev.get("mac", "")
        self.table.setItem(row, 2, QTableWidgetItem(str(mac)))

        # Hostname
        hostname = dev.get("hostname", "")
        self.table.setItem(row, 3, QTableWidgetItem(str(hostname)))

        # Vendor
        vendor = dev.get("vendor", "")
        self.table.setItem(row, 4, QTableWidgetItem(str(vendor)))

        # Status
        status = dev.get("status", "unknown")
        status_item = QTableWidgetItem(str(status))
        if status == "up":
            status_item.setForeground(Qt.GlobalColor.green)
        elif status == "down":
            status_item.setForeground(Qt.GlobalColor.red)
        self.table.setItem(row, 5, status_item)

        # Latency
        latency = dev.get("latency_ms", "")
        if latency:
            try:
                latency_val = float(latency)
                latency_item = QTableWidgetItem(f"{latency_val:.2f}")
                # Color code latency
                if latency_val > 100:
                    latency_item.setForeground(Qt.GlobalColor.red)
                elif latency_val > 50:
                    latency_item.setForeground(Qt.GlobalColor.darkYellow)
                else:
                    latency_item.setForeground(Qt.GlobalColor.green)
                self.table.setItem(row, 6, latency_item)
            except (ValueError, TypeError):
                self.table.setItem(row, 6, QTableWidgetItem(str(latency)))
        else:
            self.table.setItem(row, 6, QTableWidgetItem(""))

        # Loss
        loss = dev.get("packet_loss", "")
        if loss:
            try:
                loss_val = float(loss)
                loss_item = QTableWidgetItem(f"{loss_val:.1f}%")
                if loss_val > 10:
                    loss_item.setForeground(Qt.GlobalColor.red)
                elif loss_val > 0:
                    loss_item.setForeground(Qt.GlobalColor.darkYellow)
                self.table.setItem(row, 7, loss_item)
            except (ValueError, TypeError):
                self.table.setItem(row, 7, QTableWidgetItem(str(loss)))
        else:
            self.table.setItem(row, 7, QTableWidgetItem(""))

    def clear(self) -> None:
        """Clear all rows from the table."""
        self.table.setRowCount(0)
        self._devices = []

    def get_selected_device_id(self) -> str:
        """Get the ID of the currently selected device."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            return ""

        item = self.table.item(selected_row, 0)
        return item.text() if item else ""
