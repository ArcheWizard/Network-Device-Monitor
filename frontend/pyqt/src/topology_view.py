"""Network topology visualization widget using PyQtGraph and NetworkX."""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

import networkx as nx
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPen
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class TopologyView(QWidget):
    """Interactive network topology visualization widget."""

    device_selected = pyqtSignal(str)  # Emits device_id when clicked

    def __init__(self, parent=None):
        super().__init__(parent)

        # Graph data
        self.graph = nx.Graph()
        self.devices: Dict[str, Dict[str, Any]] = {}
        self.device_positions: Dict[str, tuple[float, float]] = {}

        # Layout algorithm
        self.layout_algorithm = "spring"  # spring, circular, random, hierarchical

        # Create UI
        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        # Top toolbar
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        # Layout selector
        toolbar_layout.addWidget(QLabel("Layout:"))
        self.layout_selector = QComboBox()
        self.layout_selector.addItems(
            ["Spring", "Circular", "Random", "Hierarchical", "Shell"]
        )
        self.layout_selector.currentTextChanged.connect(self.on_layout_changed)
        toolbar_layout.addWidget(self.layout_selector)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.update_layout)
        toolbar_layout.addWidget(self.refresh_btn)

        # Reset view button
        self.reset_btn = QPushButton("Reset View")
        self.reset_btn.clicked.connect(self.reset_view)
        toolbar_layout.addWidget(self.reset_btn)

        toolbar_layout.addStretch()
        toolbar.setLayout(toolbar_layout)

        # Graph view
        self.graph_widget = pg.GraphicsLayoutWidget()
        self.view_box = self.graph_widget.addViewBox()
        self.view_box.setAspectLocked(True)

        # Enable mouse interaction
        self.view_box.setMenuEnabled(False)
        self.view_box.setMouseEnabled(x=True, y=True)

        # Scatter plot for nodes
        self.node_plot = pg.ScatterPlotItem(
            size=20,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(100, 200, 255, 200),
            hoverable=True,
            hoverPen=pg.mkPen("y", width=2),
            hoverBrush=pg.mkBrush(255, 255, 100, 255),
        )
        self.node_plot.sigClicked.connect(self.on_node_clicked)
        self.view_box.addItem(self.node_plot)

        # Plot for edges
        self.edge_plot = pg.PlotDataItem(
            pen=pg.mkPen(color=(150, 150, 150), width=1), connect="pairs"
        )
        self.view_box.addItem(self.edge_plot)

        # Text labels for nodes
        self.labels: List[pg.TextItem] = []

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(toolbar)
        layout.addWidget(self.graph_widget)
        self.setLayout(layout)

    def on_layout_changed(self, layout_name: str) -> None:
        """Handle layout algorithm change."""
        self.layout_algorithm = layout_name.lower()
        self.update_layout()

    def add_device(self, device: Dict[str, Any]) -> None:
        """Add or update a device in the topology."""
        device_id = device.get("mac") or device.get("id") or device.get("ip")
        if not device_id:
            return

        self.devices[device_id] = device

        # Add node to graph
        if not self.graph.has_node(device_id):
            self.graph.add_node(device_id)
            logger.debug(f"Added device {device_id} to topology")

        # Update node attributes
        self.graph.nodes[device_id].update(
            {
                "ip": device.get("ip", ""),
                "hostname": device.get("hostname", ""),
                "status": device.get("status", "unknown"),
                "vendor": device.get("vendor", ""),
            }
        )

    def remove_device(self, device_id: str) -> None:
        """Remove a device from the topology."""
        if device_id in self.devices:
            del self.devices[device_id]

        if self.graph.has_node(device_id):
            self.graph.remove_node(device_id)
            logger.debug(f"Removed device {device_id} from topology")

    def add_connection(self, device1_id: str, device2_id: str) -> None:
        """Add a connection between two devices."""
        if self.graph.has_node(device1_id) and self.graph.has_node(device2_id):
            if not self.graph.has_edge(device1_id, device2_id):
                self.graph.add_edge(device1_id, device2_id)
                logger.debug(f"Added connection {device1_id} <-> {device2_id}")

    def remove_connection(self, device1_id: str, device2_id: str) -> None:
        """Remove a connection between two devices."""
        if self.graph.has_edge(device1_id, device2_id):
            self.graph.remove_edge(device1_id, device2_id)
            logger.debug(f"Removed connection {device1_id} <-> {device2_id}")

    def update_layout(self) -> None:
        """Update the graph layout and redraw."""
        if len(self.graph.nodes) == 0:
            # No devices to display
            self.node_plot.setData([], [])
            self.edge_plot.setData([], [])
            return

        # Calculate layout positions
        try:
            if self.layout_algorithm == "spring":
                pos = nx.spring_layout(self.graph, k=2, iterations=50, scale=100)
            elif self.layout_algorithm == "circular":
                pos = nx.circular_layout(self.graph, scale=100)
            elif self.layout_algorithm == "random":
                pos = {}
                for node in self.graph.nodes():
                    import random
                    pos[node] = (random.uniform(-100, 100), random.uniform(-100, 100))
            elif self.layout_algorithm == "hierarchical":
                pos = nx.kamada_kawai_layout(self.graph, scale=100)
            elif self.layout_algorithm == "shell":
                pos = nx.shell_layout(self.graph, scale=100)
            else:
                pos = nx.spring_layout(self.graph, scale=100)

            self.device_positions = pos

        except Exception as e:
            logger.exception(f"Error calculating layout: {e}")
            return

        # Prepare node data
        node_x = []
        node_y = []
        node_colors = []
        node_data = []

        for node_id, (x, y) in pos.items():
            node_x.append(x)
            node_y.append(y)

            # Color based on status
            device = self.devices.get(node_id, {})
            status = device.get("status", "unknown")

            if status == "up":
                color = QColor(100, 255, 100, 200)  # Green
            elif status == "down":
                color = QColor(255, 100, 100, 200)  # Red
            else:
                color = QColor(200, 200, 200, 200)  # Gray

            node_colors.append(QBrush(color))
            node_data.append({"device_id": node_id, "device": device})

        # Update node plot
        self.node_plot.setData(
            x=node_x,
            y=node_y,
            brush=node_colors,
            data=node_data,
        )

        # Prepare edge data
        edge_x = []
        edge_y = []

        for edge in self.graph.edges():
            if edge[0] in pos and edge[1] in pos:
                x1, y1 = pos[edge[0]]
                x2, y2 = pos[edge[1]]
                edge_x.extend([x1, x2])
                edge_y.extend([y1, y2])

        # Update edge plot
        self.edge_plot.setData(x=edge_x, y=edge_y)

        # Update labels
        self._update_labels(pos)

        logger.debug(f"Updated topology with {len(self.graph.nodes)} nodes")

    def _update_labels(self, pos: Dict[str, tuple[float, float]]) -> None:
        """Update text labels for nodes."""
        # Clear existing labels
        for label in self.labels:
            self.view_box.removeItem(label)
        self.labels.clear()

        # Add new labels
        for node_id, (x, y) in pos.items():
            device = self.devices.get(node_id, {})
            label_text = device.get("hostname") or device.get("ip") or node_id[:8]

            label = pg.TextItem(text=label_text, anchor=(0.5, 1.5))
            label.setPos(x, y)
            self.view_box.addItem(label)
            self.labels.append(label)

    def on_node_clicked(self, plot, points) -> None:
        """Handle node click event."""
        if len(points) > 0:
            point = points[0]
            data = point.data()
            if data and "device_id" in data:
                device_id = data["device_id"]
                self.device_selected.emit(device_id)
                logger.debug(f"Node clicked: {device_id}")

    def reset_view(self) -> None:
        """Reset view to fit all nodes."""
        self.view_box.autoRange()

    def clear(self) -> None:
        """Clear all devices and connections."""
        self.graph.clear()
        self.devices.clear()
        self.device_positions.clear()
        self.node_plot.setData([], [])
        self.edge_plot.setData([], [])
        for label in self.labels:
            self.view_box.removeItem(label)
        self.labels.clear()

    def update_from_devices(self, devices: List[Dict[str, Any]]) -> None:
        """Update topology from a list of devices."""
        # Clear existing
        self.clear()

        # Add all devices
        for device in devices:
            self.add_device(device)

        # Infer connections (devices on same subnet are connected to a virtual gateway)
        # This is a simple heuristic - in reality, you'd use LLDP/CDP data
        self._infer_connections()

        # Update layout
        self.update_layout()

    def _infer_connections(self) -> None:
        """Infer connections between devices (simplified heuristic)."""
        # Group devices by subnet
        subnets: Dict[str, List[str]] = {}

        for device_id, device in self.devices.items():
            ip = device.get("ip", "")
            if ip:
                # Extract /24 subnet
                parts = ip.split(".")
                if len(parts) >= 3:
                    subnet = ".".join(parts[:3])
                    if subnet not in subnets:
                        subnets[subnet] = []
                    subnets[subnet].append(device_id)

        # Create star topology for each subnet (gateway in center)
        for subnet, device_ids in subnets.items():
            if len(device_ids) > 1:
                # Add virtual gateway node
                gateway_id = f"Gateway-{subnet}"
                if not self.graph.has_node(gateway_id):
                    self.graph.add_node(gateway_id)
                    self.devices[gateway_id] = {
                        "id": gateway_id,
                        "ip": f"{subnet}.1",
                        "hostname": f"Gateway {subnet}",
                        "status": "up",
                        "vendor": "Virtual",
                    }

                # Connect all devices in subnet to gateway
                for device_id in device_ids:
                    self.add_connection(gateway_id, device_id)
