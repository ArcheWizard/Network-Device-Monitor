"""Tests for MainWindow UI logic."""

from __future__ import annotations

from unittest.mock import patch
import pytest
from PyQt6.QtWidgets import QApplication


# Qt application required for widget tests
@pytest.fixture(scope="module")
def qt_app():
    """Create Qt application for tests."""
    app = QApplication([])
    yield app
    app.quit()


class TestMainWindow:
    """Tests for MainWindow UI."""

    def test_window_initialization(self, qt_app):
        """Test MainWindow initializes correctly."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                assert window.windowTitle() == "Network Device Monitor"
                assert window.base_url == "http://test:8000"
                assert window.table.rowCount() == 0
                assert window.table.columnCount() == 8

    def test_populate_devices(self, qt_app):
        """Test populate_devices fills table correctly."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                devices = [
                    {
                        "id": "aa:bb:cc:dd:ee:ff",
                        "ip": "192.168.1.10",
                        "mac": "aa:bb:cc:dd:ee:ff",
                        "hostname": "device1",
                        "vendor": "VendorA",
                        "status": "up",
                    },
                    {
                        "id": "11:22:33:44:55:66",
                        "ip": "192.168.1.20",
                        "mac": "11:22:33:44:55:66",
                        "hostname": "device2",
                        "vendor": "VendorB",
                        "status": "down",
                    },
                ]

                window.populate_devices(devices)

                assert window.table.rowCount() == 2
                item_00 = window.table.item(0, 0)
                item_01 = window.table.item(0, 1)
                item_13 = window.table.item(1, 3)
                assert item_00 is not None and item_00.text() == "aa:bb:cc:dd:ee:ff"
                assert item_01 is not None and item_01.text() == "192.168.1.10"
                assert item_13 is not None and item_13.text() == "device2"

    def test_upsert_device_row_new_device(self, qt_app):
        """Test upsert_device_row creates new row for new device."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                device = {
                    "id": "test:device",
                    "ip": "192.168.1.100",
                    "mac": "aa:bb:cc:dd:ee:ff",
                    "hostname": "test",
                    "vendor": "TestVendor",
                    "status": "up",
                }

                window.upsert_device_row(device)

                assert window.table.rowCount() == 1
                assert "test:device" in window._rows_by_id
                item = window.table.item(0, 0)
                assert item is not None and item.text() == "test:device"

    def test_upsert_device_row_update_existing(self, qt_app):
        """Test upsert_device_row updates existing device."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                device_v1 = {
                    "id": "test:device",
                    "ip": "192.168.1.100",
                    "hostname": "oldname",
                    "status": "unknown",
                }
                window.upsert_device_row(device_v1)

                device_v2 = {
                    "id": "test:device",
                    "ip": "192.168.1.100",
                    "hostname": "newname",
                    "vendor": "NewVendor",
                    "status": "up",
                }
                window.upsert_device_row(device_v2)

                # Should still be 1 row, just updated
                assert window.table.rowCount() == 1
                item_03 = window.table.item(0, 3)
                item_04 = window.table.item(0, 4)
                assert item_03 is not None and item_03.text() == "newname"
                assert item_04 is not None and item_04.text() == "NewVendor"

    def test_on_event_device_up(self, qt_app):
        """Test on_event handles device_up event."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                # Pre-populate device
                window.upsert_device_row(
                    {"id": "dev1", "ip": "192.168.1.10", "status": "down"}
                )

                # Send device_up event
                window.on_event(
                    {"type": "device_up", "device_id": "dev1", "ip": "192.168.1.10"}
                )

                # Check status column updated
                item = window.table.item(0, 5)
                assert item is not None and item.text() == "up"

    def test_on_event_latency(self, qt_app):
        """Test on_event handles latency event."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                # Pre-populate device
                window.upsert_device_row({"id": "dev1", "ip": "192.168.1.10"})

                # Send latency event
                window.on_event(
                    {
                        "type": "latency",
                        "device_id": "dev1",
                        "latency_avg": 12.5,
                        "packet_loss": 0.02,
                    }
                )

                # Check latency columns updated
                item_avg = window.table.item(0, 6)
                item_loss = window.table.item(0, 7)
                assert item_avg is not None and item_avg.text() == "12.5"
                assert item_loss is not None and item_loss.text() == "0.02"

    def test_on_event_device_discovered(self, qt_app):
        """Test on_event handles device_discovered event with device object."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh"):
            with patch.object(MainWindow, "start_stream"):
                window = MainWindow("http://test:8000")

                # Send device_discovered event
                window.on_event(
                    {
                        "type": "device_discovered",
                        "device": {
                            "id": "new:device",
                            "ip": "192.168.1.200",
                            "hostname": "discovered",
                        },
                    }
                )

                # Check device was added
                assert window.table.rowCount() == 1
                item_00 = window.table.item(0, 0)
                item_03 = window.table.item(0, 3)
                assert item_00 is not None and item_00.text() == "new:device"
                assert item_03 is not None and item_03.text() == "discovered"

    def test_button_clicks(self, qt_app):
        """Test button click handlers are connected."""
        from src.main_window import MainWindow

        with patch.object(MainWindow, "on_refresh") as mock_refresh:
            with patch.object(MainWindow, "start_stream"):
                with patch.object(MainWindow, "on_scan") as mock_scan:
                    window = MainWindow("http://test:8000")

                    # Click refresh button
                    window.refresh_btn.click()
                    assert mock_refresh.call_count == 2  # once on init, once on click

                    # Click scan button
                    window.scan_btn.click()
                    mock_scan.assert_called_once()
