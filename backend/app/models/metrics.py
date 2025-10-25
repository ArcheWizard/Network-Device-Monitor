from pydantic import BaseModel


class LatencyPoint(BaseModel):
    ts: int
    ms: float
    loss: float
