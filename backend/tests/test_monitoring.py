"""Tests for monitoring service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.monitoring import ping_device


class TestPingDevice:
    """Tests for ping_device function."""

    @pytest.mark.asyncio
    async def test_ping_device_success(self):
        """Test successful ping with latency metrics."""
        # Mock successful ping output
        ping_output = b"""PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.
64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=0.123 ms
64 bytes from 192.168.1.1: icmp_seq=2 ttl=64 time=0.456 ms
64 bytes from 192.168.1.1: icmp_seq=3 ttl=64 time=0.789 ms
64 bytes from 192.168.1.1: icmp_seq=4 ttl=64 time=1.012 ms

--- 192.168.1.1 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3005ms
rtt min/avg/max/mdev = 0.123/0.595/1.012/0.334 ms
"""

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(ping_output, b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await ping_device("192.168.1.1", count=4, timeout=2.0)

            assert result["ip"] == "192.168.1.1"
            assert result["status"] == "up"
            assert result["latency_min"] == 0.123
            assert result["latency_avg"] == 0.595
            assert result["latency_max"] == 1.012
            assert result["packet_loss"] == 0.0

    @pytest.mark.asyncio
    async def test_ping_device_partial_loss(self):
        """Test ping with partial packet loss."""
        ping_output = b"""PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.
64 bytes from 192.168.1.1: icmp_seq=1 ttl=64 time=0.123 ms
64 bytes from 192.168.1.1: icmp_seq=2 ttl=64 time=0.456 ms

--- 192.168.1.1 ping statistics ---
4 packets transmitted, 2 received, 50% packet loss, time 3005ms
rtt min/avg/max/mdev = 0.123/0.289/0.456/0.167 ms
"""

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(ping_output, b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await ping_device("192.168.1.1")

            assert result["status"] == "up"
            assert result["packet_loss"] == 50.0
            assert result["latency_avg"] == 0.289

    @pytest.mark.asyncio
    async def test_ping_device_down(self):
        """Test ping failure (device down)."""
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"Network unreachable"))
        mock_proc.returncode = 1

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await ping_device("192.168.1.99")

            assert result["ip"] == "192.168.1.99"
            assert result["status"] == "down"
            assert result["latency_avg"] is None
            assert result["latency_min"] is None
            assert result["latency_max"] is None
            assert result["packet_loss"] == 100.0

    @pytest.mark.asyncio
    async def test_ping_device_100_percent_loss(self):
        """Test ping with 100% packet loss."""
        ping_output = b"""PING 192.168.1.1 (192.168.1.1) 56(84) bytes of data.

--- 192.168.1.1 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3005ms
"""

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(ping_output, b""))
        mock_proc.returncode = 0

        with patch("asyncio.create_subprocess_exec", return_value=mock_proc):
            result = await ping_device("192.168.1.1")

            assert result["status"] == "down"
            assert result["packet_loss"] == 100.0

    @pytest.mark.asyncio
    async def test_ping_device_exception(self):
        """Test ping with exception."""
        with patch(
            "asyncio.create_subprocess_exec", side_effect=Exception("Subprocess error")
        ):
            result = await ping_device("192.168.1.1")

            assert result["ip"] == "192.168.1.1"
            assert result["status"] == "error"
            assert result["packet_loss"] == 100.0
