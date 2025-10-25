from fastapi import FastAPI
from .api.routers import devices, metrics, ws
from .scheduler.jobs import init_scheduler
from .storage.sqlite import init_sqlite
from .storage.influx import init_influx
from .config import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite repository and attach to app state
    try:
        repo = await init_sqlite()
        app.state.inventory_repo = repo
    except Exception as e:
        # Non-fatal for now; endpoints may fallback to in-memory stubs
        print(f"[startup] SQLite init failed: {e}")

    # Initialize InfluxDB writer if configured
    if settings.INFLUX_URL and settings.INFLUX_TOKEN:
        try:
            influx_writer = init_influx(
                url=settings.INFLUX_URL,
                token=settings.INFLUX_TOKEN,
                org=settings.INFLUX_ORG or "local",
                bucket=settings.INFLUX_BUCKET or "network_metrics",
            )
            app.state.influx_writer = influx_writer
            if influx_writer:
                print(f"[startup] InfluxDB connected at {settings.INFLUX_URL}")
        except Exception as e:
            print(f"[startup] InfluxDB init failed: {e}")
    else:
        print("[startup] InfluxDB not configured (set INFLUX_URL and INFLUX_TOKEN)")

    await init_scheduler(app)
    yield
    # Optional teardown here


app = FastAPI(title="Network Device Monitor", version="0.1.0", lifespan=lifespan)

app.include_router(devices.router, prefix="/api", tags=["devices"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])
app.include_router(ws.router, tags=["ws"])


@app.get("/api/health")
async def health():
    return {"status": "ok"}
