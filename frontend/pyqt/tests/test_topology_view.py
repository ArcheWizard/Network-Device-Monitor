"""Tests for topology view widget."""

import pytest
from PyQt6.QtWidgets import QApplication

from src.topology_view import TopologyView


@pytest.fixture
def topology_view(qtbot):
    """Create topology view widget for testing."""
    view = TopologyView()
    qtbot.addWidget(view)
    return view


def test_topology_view_creation(topology_view):
    """Test that topology view is created successfully."""
    assert topology_view is not None
    assert topology_view.graph is not None


def test_add_device(topology_view):
    """Test adding a device to topology."""
    device = {
        "id": "test-1",
        "ip": "192.168.1.100",
        "mac": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "up",
    }

    topology_view.add_device(device)

    assert "AA:BB:CC:DD:EE:FF" in topology_view.devices
    assert topology_view.graph.has_node("AA:BB:CC:DD:EE:FF")


def test_remove_device(topology_view):
    """Test removing a device from topology."""
    device = {
        "id": "test-1",
        "ip": "192.168.1.100",
        "mac": "AA:BB:CC:DD:EE:FF",
        "hostname": "test-device",
        "status": "up",
    }

    topology_view.add_device(device)
    assert "AA:BB:CC:DD:EE:FF" in topology_view.devices

    topology_view.remove_device("AA:BB:CC:DD:EE:FF")
    assert "AA:BB:CC:DD:EE:FF" not in topology_view.devices
    assert not topology_view.graph.has_node("AA:BB:CC:DD:EE:FF")


def test_add_connection(topology_view):
    """Test adding a connection between devices."""
    device1 = {
        "id": "test-1",
        "ip": "192.168.1.100",
        "mac": "AA:BB:CC:DD:EE:11",
        "status": "up",
    }
    device2 = {
        "id": "test-2",
        "ip": "192.168.1.101",
        "mac": "AA:BB:CC:DD:EE:22",
        "status": "up",
    }

    topology_view.add_device(device1)
    topology_view.add_device(device2)
    topology_view.add_connection("AA:BB:CC:DD:EE:11", "AA:BB:CC:DD:EE:22")

    assert topology_view.graph.has_edge("AA:BB:CC:DD:EE:11", "AA:BB:CC:DD:EE:22")


def test_clear(topology_view):
    """Test clearing all devices and connections."""
    device1 = {"id": "test-1", "mac": "AA:BB:CC:DD:EE:11", "status": "up"}
    device2 = {"id": "test-2", "mac": "AA:BB:CC:DD:EE:22", "status": "up"}

    topology_view.add_device(device1)
    topology_view.add_device(device2)
    topology_view.add_connection("AA:BB:CC:DD:EE:11", "AA:BB:CC:DD:EE:22")

    assert len(topology_view.devices) == 2

    topology_view.clear()

    assert len(topology_view.devices) == 0
    assert len(topology_view.graph.nodes) == 0
    assert len(topology_view.graph.edges) == 0


def test_update_from_devices(topology_view):
    """Test updating topology from device list."""
    devices = [
        {"id": "test-1", "ip": "192.168.1.100", "mac": "AA:BB:CC:DD:EE:11", "status": "up"},
        {"id": "test-2", "ip": "192.168.1.101", "mac": "AA:BB:CC:DD:EE:22", "status": "up"},
        {"id": "test-3", "ip": "192.168.1.102", "mac": "AA:BB:CC:DD:EE:33", "status": "down"},
    ]

    topology_view.update_from_devices(devices)

    assert len(topology_view.devices) >= 3  # May include virtual gateway nodes
    assert topology_view.graph.has_node("AA:BB:CC:DD:EE:11")
    assert topology_view.graph.has_node("AA:BB:CC:DD:EE:22")
    assert topology_view.graph.has_node("AA:BB:CC:DD:EE:33")


def test_layout_change(topology_view, qtbot):
    """Test changing layout algorithm."""
    devices = [
        {"id": "test-1", "ip": "192.168.1.100", "mac": "AA:BB:CC:DD:EE:11", "status": "up"},
        {"id": "test-2", "ip": "192.168.1.101", "mac": "AA:BB:CC:DD:EE:22", "status": "up"},
    ]

    topology_view.update_from_devices(devices)

    # Test different layouts
    for layout in ["Spring", "Circular", "Hierarchical"]:
        topology_view.layout_selector.setCurrentText(layout)
        # Give it time to update
        qtbot.wait(100)
        assert topology_view.layout_algorithm == layout.lower()
