"""Tests for device identification service."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.identification import identify_device, vendor_from_mac


class TestVendorFromMac:
    """Tests for vendor_from_mac function."""

    @pytest.mark.asyncio
    async def test_vendor_from_mac_found(self):
        """Test successful vendor lookup."""
        with patch(
            "app.services.identification.lookup_vendor", return_value="Test Vendor"
        ):
            vendor = await vendor_from_mac("00:11:22:33:44:55")
            assert vendor == "Test Vendor"

    @pytest.mark.asyncio
    async def test_vendor_from_mac_not_found(self):
        """Test vendor lookup with unknown MAC."""
        with patch("app.services.identification.lookup_vendor", return_value=None):
            vendor = await vendor_from_mac("99:88:77:66:55:44")
            assert vendor is None


class TestIdentifyDevice:
    """Tests for identify_device function."""

    @pytest.mark.asyncio
    async def test_identify_device_full(self):
        """Test full device identification with OUI and SNMP."""
        mock_snmp_data = {
            "hostname": "test-device",
            "description": "Test Device Description",
            "uptime": "12345678",
            "contact": "admin@test.com",
            "location": "Data Center",
            "object_id": "1.3.6.1.4.1.9",
        }

        with patch(
            "app.services.identification.lookup_vendor", return_value="Test Vendor"
        ):
            with patch(
                "app.services.identification.snmp_query",
                new=AsyncMock(return_value=mock_snmp_data),
            ):
                result = await identify_device(
                    ip="192.168.1.100",
                    mac="00:11:22:33:44:55",
                    use_oui=True,
                    use_snmp=True,
                )

                assert result["vendor"] == "Test Vendor"
                assert result["hostname"] == "test-device"
                assert result["description"] == "Test Device Description"
                assert result["uptime"] == "12345678"
                assert result["contact"] == "admin@test.com"
                assert result["location"] == "Data Center"
                assert result["object_id"] == "1.3.6.1.4.1.9"

    @pytest.mark.asyncio
    async def test_identify_device_oui_only(self):
        """Test device identification with OUI only."""
        with patch(
            "app.services.identification.lookup_vendor", return_value="Test Vendor"
        ):
            result = await identify_device(
                ip="192.168.1.100",
                mac="00:11:22:33:44:55",
                use_oui=True,
                use_snmp=False,
            )

            assert result["vendor"] == "Test Vendor"
            assert result["hostname"] is None
            assert result["description"] is None

    @pytest.mark.asyncio
    async def test_identify_device_snmp_only(self):
        """Test device identification with SNMP only."""
        mock_snmp_data = {
            "hostname": "test-device",
            "description": "Test Device",
            "uptime": "12345",
            "contact": None,
            "location": None,
            "object_id": None,
        }

        with patch(
            "app.services.identification.snmp_query",
            new=AsyncMock(return_value=mock_snmp_data),
        ):
            result = await identify_device(
                ip="192.168.1.100",
                mac="00:11:22:33:44:55",
                use_oui=False,
                use_snmp=True,
            )

            assert result["vendor"] is None
            assert result["hostname"] == "test-device"
            assert result["description"] == "Test Device"

    @pytest.mark.asyncio
    async def test_identify_device_no_mac(self):
        """Test device identification without MAC address."""
        mock_snmp_data = {
            "hostname": "test-device",
            "description": None,
            "uptime": None,
            "contact": None,
            "location": None,
            "object_id": None,
        }

        with patch(
            "app.services.identification.snmp_query",
            new=AsyncMock(return_value=mock_snmp_data),
        ):
            result = await identify_device(
                ip="192.168.1.100",
                mac=None,
                use_oui=True,
                use_snmp=True,
            )

            assert result["vendor"] is None  # No MAC, no OUI lookup
            assert result["hostname"] == "test-device"

    @pytest.mark.asyncio
    async def test_identify_device_oui_failure(self):
        """Test device identification when OUI lookup fails."""
        mock_snmp_data = {
            "hostname": "test-device",
            "description": None,
            "uptime": None,
            "contact": None,
            "location": None,
            "object_id": None,
        }

        with patch(
            "app.services.identification.lookup_vendor",
            side_effect=Exception("OUI lookup failed"),
        ):
            with patch(
                "app.services.identification.snmp_query",
                new=AsyncMock(return_value=mock_snmp_data),
            ):
                result = await identify_device(
                    ip="192.168.1.100",
                    mac="00:11:22:33:44:55",
                    use_oui=True,
                    use_snmp=True,
                )

                assert result["vendor"] is None  # OUI failed
                assert result["hostname"] == "test-device"  # SNMP still works

    @pytest.mark.asyncio
    async def test_identify_device_snmp_failure(self):
        """Test device identification when SNMP query fails."""
        with patch(
            "app.services.identification.lookup_vendor", return_value="Test Vendor"
        ):
            with patch(
                "app.services.identification.snmp_query",
                new=AsyncMock(side_effect=Exception("SNMP failed")),
            ):
                result = await identify_device(
                    ip="192.168.1.100",
                    mac="00:11:22:33:44:55",
                    use_oui=True,
                    use_snmp=True,
                )

                assert result["vendor"] == "Test Vendor"  # OUI still works
                assert result["hostname"] is None  # SNMP failed

    @pytest.mark.asyncio
    async def test_identify_device_all_disabled(self):
        """Test device identification with all methods disabled."""
        result = await identify_device(
            ip="192.168.1.100",
            mac="00:11:22:33:44:55",
            use_oui=False,
            use_snmp=False,
        )

        assert result["vendor"] is None
        assert result["hostname"] is None
        assert result["description"] is None
        assert result["uptime"] is None
        assert result["contact"] is None
        assert result["location"] is None
        assert result["object_id"] is None
