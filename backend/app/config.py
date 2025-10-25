from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    NETWORK_CIDR: str = "192.168.1.0/24"
    INTERFACE: str | None = None

    SNMP_COMMUNITY: str = "public"
    SNMP_PORT: int = 161
    SNMP_TIMEOUT: float = 1.0

    INFLUX_URL: str | None = None
    INFLUX_TOKEN: str | None = None
    INFLUX_ORG: str | None = None
    INFLUX_BUCKET: str | None = None

    ALERT_LATENCY_MS: float = 200.0
    ALERT_PACKET_LOSS: float = 0.5

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
