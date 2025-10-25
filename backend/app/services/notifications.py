from typing import Literal


AlertSeverity = Literal["info", "warn", "crit"]


def notify(event: dict, severity: AlertSeverity = "info") -> None:
    # TODO: send to log/websocket/email/webhook
    _ = (event, severity)
    return None
