import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Network Configuration
    NETWORK_CIDR: str = "192.168.1.0/24"
    INTERFACE: str | None = None

    # SNMP Configuration
    SNMP_COMMUNITY: str = "public"
    SNMP_PORT: int = 161
    SNMP_TIMEOUT: float = 1.0

    # InfluxDB Configuration
    INFLUX_URL: str | None = None
    INFLUX_TOKEN: str | None = None
    INFLUX_ORG: str | None = None
    INFLUX_BUCKET: str | None = None

    # Alert Thresholds
    ALERT_LATENCY_MS: float = 200.0
    ALERT_PACKET_LOSS: float = 0.5

    # Authentication & Authorization
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60  # 1 hour
    REQUIRE_AUTH: bool = False  # Set to True to enable authentication

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
