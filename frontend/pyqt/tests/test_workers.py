"""Tests for QThread worker classes."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
import pytest
from PyQt6.QtCore import QCoreApplication
from PyQt6.QtTest import QSignalSpy


# Qt application required for QThread tests
@pytest.fixture(scope="module")
def qt_app():
    """Create Qt application for tests."""
    app = QCoreApplication([])
    yield app


class TestFetchDevicesWorker:
    """Tests for FetchDevicesWorker."""

    def test_worker_emits_result_on_success(self, qt_app):
        """Test worker emits result signal with device list."""
        from src.main_window import FetchDevicesWorker

        mock_devices = [{"id": "test", "ip": "192.168.1.10"}]

        with patch("src.api_client.APIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_devices = AsyncMock(return_value=mock_devices)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            worker = FetchDevicesWorker("http://test:8000")
            result_spy = QSignalSpy(worker.result)
            error_spy = QSignalSpy(worker.error)

            worker.run()

            # Verify result signal was emitted
            assert len(result_spy) == 1
            assert result_spy[0][0] == mock_devices
            assert len(error_spy) == 0

    def test_worker_emits_error_on_exception(self, qt_app):
        """Test worker emits error signal on exception."""
        from src.main_window import FetchDevicesWorker

        with patch("src.api_client.APIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.fetch_devices = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            worker = FetchDevicesWorker("http://test:8000")
            result_spy = QSignalSpy(worker.result)
            error_spy = QSignalSpy(worker.error)

            worker.run()

            # Verify error signal was emitted
            assert len(result_spy) == 0
            assert len(error_spy) == 1
            assert "Connection failed" in error_spy[0][0]


class TestTriggerScanWorker:
    """Tests for TriggerScanWorker."""

    def test_worker_triggers_scan_successfully(self, qt_app):
        """Test worker triggers scan and emits done signal."""
        from src.main_window import TriggerScanWorker

        mock_result = {"count": 3, "devices": []}

        with patch("src.api_client.APIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.trigger_scan = AsyncMock(return_value=mock_result)
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            worker = TriggerScanWorker("http://test:8000")
            done_spy = QSignalSpy(worker.done)
            error_spy = QSignalSpy(worker.error)

            worker.run()

            # Verify done signal was emitted
            assert len(done_spy) == 1
            assert done_spy[0][0] == mock_result
            assert len(error_spy) == 0


class TestEventStreamWorker:
    """Tests for EventStreamWorker."""

    def test_worker_streams_events(self, qt_app):
        """Test worker streams WebSocket events."""
        from src.main_window import EventStreamWorker

        async def mock_stream():
            yield {"type": "hello"}
            yield {"type": "device_up", "device_id": "test"}

        with patch("src.api_client.APIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream_events = mock_stream
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            worker = EventStreamWorker("http://test:8000")
            message_spy = QSignalSpy(worker.message)

            worker.run()

            # Verify messages were emitted
            assert len(message_spy) == 2
            assert message_spy[0][0]["type"] == "hello"
            assert message_spy[1][0]["type"] == "device_up"

    def test_worker_stops_on_stop_flag(self, qt_app):
        """Test worker stops when stop() is called."""
        from src.main_window import EventStreamWorker

        async def mock_stream():
            for i in range(100):
                yield {"type": "test", "count": i}

        with patch("src.api_client.APIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.stream_events = mock_stream
            mock_client.aclose = AsyncMock()
            mock_client_class.return_value = mock_client

            worker = EventStreamWorker("http://test:8000")
            message_spy = QSignalSpy(worker.message)

            # Set stop flag immediately
            worker._stop = True
            worker.run()

            # Should not emit many messages since we stopped early
            assert len(message_spy) < 10
