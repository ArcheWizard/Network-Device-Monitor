from pydantic import BaseModel, Field
from typing import Optional, Literal


class Device(BaseModel):
    id: str  # stable id (mac or mac+ip)
    ip: Optional[str] = None
    mac: Optional[str] = None
    hostname: Optional[str] = None
    vendor: Optional[str] = None
    device_type: Optional[str] = None
    status: Optional[Literal["up", "down", "unknown"]] = "unknown"
    first_seen: Optional[int] = Field(default=None, description="unix ts")
    last_seen: Optional[int] = Field(default=None, description="unix ts")
    tags: dict[str, str] = {}
