"""Tests for OUI lookup functionality."""

from __future__ import annotations

import csv
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.utils.oui import (
    _normalize_mac_prefix,
    download_oui_database,
    load_oui_cache,
    lookup_vendor,
)


class TestMacNormalization:
    """Tests for MAC address normalization."""

    def test_normalize_colon_format(self):
        assert _normalize_mac_prefix("aa:bb:cc:dd:ee:ff") == "AABBCC"

    def test_normalize_dash_format(self):
        assert _normalize_mac_prefix("AA-BB-CC-DD-EE-FF") == "AABBCC"

    def test_normalize_dot_format(self):
        assert _normalize_mac_prefix("aabbcc.ddeeff") == "AABBCC"

    def test_normalize_no_separator(self):
        assert _normalize_mac_prefix("aabbccddeeff") == "AABBCC"

    def test_normalize_short_mac(self):
        # Short MACs should return what's available
        assert _normalize_mac_prefix("aa:bb") == "AABB"

    def test_normalize_empty(self):
        assert _normalize_mac_prefix("") == ""

    def test_normalize_uppercase(self):
        assert _normalize_mac_prefix("FF:EE:DD:CC:BB:AA") == "FFEEDD"


class TestOuiLookup:
    """Tests for OUI vendor lookup."""

    @pytest.fixture
    def mock_cache_file(self, tmp_path: Path):
        """Create a temporary OUI cache file."""
        cache_file = tmp_path / "oui_cache.csv"
        with cache_file.open("w", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["prefix", "vendor"])
            writer.writerow(["001122", "Vendor A"])
            writer.writerow(["AABBCC", "Vendor B"])
            writer.writerow(["DDEEFF", "Vendor C"])
        return cache_file

    def test_lookup_vendor_found(self, mock_cache_file: Path):
        """Test successful vendor lookup."""
        with patch("app.utils.oui.OUI_CACHE_FILE", mock_cache_file):
            load_oui_cache()
            assert lookup_vendor("00:11:22:33:44:55") == "Vendor A"
            assert lookup_vendor("AA-BB-CC-DD-EE-FF") == "Vendor B"
            assert lookup_vendor("ddeeff112233") == "Vendor C"

    def test_lookup_vendor_not_found(self, mock_cache_file: Path):
        """Test vendor lookup with unknown MAC."""
        with patch("app.utils.oui.OUI_CACHE_FILE", mock_cache_file):
            load_oui_cache()
            assert lookup_vendor("99:88:77:66:55:44") is None

    def test_lookup_vendor_invalid_mac(self, mock_cache_file: Path):
        """Test vendor lookup with invalid MAC."""
        with patch("app.utils.oui.OUI_CACHE_FILE", mock_cache_file):
            load_oui_cache()
            assert lookup_vendor("invalid") is None
            assert lookup_vendor("") is None


class TestOuiDownload:
    """Tests for OUI database download."""

    @pytest.mark.asyncio
    async def test_download_success_ieee(self, tmp_path: Path):
        """Test successful download from IEEE."""
        cache_file = tmp_path / "oui_cache.csv"

        # Mock IEEE CSV response
        ieee_csv = 'Registry,Assignment,Organization Name,Organization Address\nMA-L,00-11-22,"Test Vendor","123 Main St"'

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = ieee_csv

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.utils.oui.OUI_CACHE_FILE", cache_file):
            # Fix: Use correct import path - httpx is imported inside the function
            with patch("httpx.AsyncClient", return_value=mock_client):
                success = await download_oui_database(force=True)
                assert success
                assert cache_file.exists()

                # Verify cache contents
                with cache_file.open(encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 1
                    assert rows[0]["prefix"] == "001122"
                    assert rows[0]["vendor"] == "Test Vendor"

    @pytest.mark.asyncio
    async def test_download_skip_existing(self, tmp_path: Path):
        """Test skipping download when cache exists."""
        cache_file = tmp_path / "oui_cache.csv"
        cache_file.touch()

        with patch("app.utils.oui.OUI_CACHE_FILE", cache_file):
            success = await download_oui_database(force=False)
            assert success

    @pytest.mark.asyncio
    async def test_download_fallback_to_wireshark(self, tmp_path: Path):
        """Test fallback to Wireshark manuf when IEEE fails."""
        cache_file = tmp_path / "oui_cache.csv"

        # Mock Wireshark manuf response
        wireshark_manuf = (
            "00:11:22\tTest Vendor\n# Comment line\nAA:BB:CC\tAnother Vendor"
        )

        mock_ieee_response = MagicMock()
        mock_ieee_response.raise_for_status = MagicMock(
            side_effect=Exception("IEEE failed")
        )

        mock_ws_response = MagicMock()
        mock_ws_response.raise_for_status = MagicMock()
        mock_ws_response.text = wireshark_manuf

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_ieee_response, mock_ws_response])

        with patch("app.utils.oui.OUI_CACHE_FILE", cache_file):
            with patch("httpx.AsyncClient", return_value=mock_client):
                success = await download_oui_database(force=True)
                assert success
                assert cache_file.exists()

                # Verify cache contents
                with cache_file.open(encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    assert len(rows) == 1
                    assert rows[0]["prefix"] == "001122"
                    assert rows[0]["vendor"] == "Test Vendor"

    @pytest.mark.asyncio
    async def test_download_failure(self, tmp_path: Path):
        """Test download failure from all sources."""
        cache_file = tmp_path / "oui_cache.csv"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock(
            side_effect=Exception("Download failed")
        )

        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch("app.utils.oui.OUI_CACHE_FILE", cache_file):
            with patch("httpx.AsyncClient", return_value=mock_client):
                success = await download_oui_database(force=True)
                assert not success
                assert not cache_file.exists()
