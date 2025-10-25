import pytest

from app.storage.sqlite import init_sqlite


@pytest.mark.asyncio
async def test_sqlite_repo_upsert_and_list():
    repo = await init_sqlite(":memory:")
    # Upsert a device
    dev = {
        "id": "aa:bb:cc:dd:ee:ff",
        "ip": "192.0.2.10",
        "mac": "aa:bb:cc:dd:ee:ff",
        "hostname": "test.local",
        "vendor": "Test",
        "device_type": "workstation",
        "first_seen": 1,
        "last_seen": 2,
        "tags": {"site": "lab"},
    }
    await repo.upsert_device(dev)

    # List
    items = await repo.list_devices()
    assert len(items) == 1
    assert items[0]["id"] == dev["id"]
    assert items[0]["ip"] == dev["ip"]
    assert items[0]["tags"]["site"] == "lab"

    # Get
    got = await repo.get_device(dev["id"])
    assert got is not None
    assert got["hostname"] == "test.local"
