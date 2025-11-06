# WebSocket Streaming

Real-time event streaming via WebSocket for live updates of network device status and metrics.

## Overview

The WebSocket endpoint (`/ws/stream`) provides real-time notifications for:

- Device discovered events
- Device status changes (up/down)
- Latency measurements
- Network events

## Quick Start

### JavaScript Client

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/stream');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data.type, data);
};

ws.onopen = () => console.log('Connected');
ws.onerror = (error) => console.error('WebSocket error:', error);
```

### Python Client

```python
import asyncio
import websockets
import json

async def listen():
    async with websockets.connect('ws://localhost:8000/ws/stream') as ws:
        async for message in ws:
            data = json.loads(message)
            print(f"Event: {data['type']}", data)

asyncio.run(listen())
```

## Message Types

### hello

Sent immediately upon connection:

```json
{
    "type": "hello",
    "ts": 1699000000
}
```

### device_discovered

Sent when a new device is found during discovery:

```json
{
    "type": "device_discovered",
    "ts": 1699000000,
    "device": {
        "id": "aa:bb:cc:dd:ee:ff",
        "ip": "192.168.1.100",
        "mac": "aa:bb:cc:dd:ee:ff",
        "hostname": "laptop.local",
        "vendor": "Apple Inc"
    }
}
```

### device_up

Sent when a device comes online:

```json
{
    "type": "device_up",
    "ts": 1699000000,
    "device_id": "192.168.1.1"
}
```

### device_down

Sent when a device goes offline:

```json
{
    "type": "device_down",
    "ts": 1699000000,
    "device_id": "192.168.1.1"
}
```

### latency

Sent after each monitoring check:

```json
{
    "type": "latency",
    "ts": 1699000000,
    "device_id": "192.168.1.1",
    "ms": 12.4,
    "loss": 0.0
}
```

## Integration Examples

### React Component

```jsx
import { useEffect, useState } from 'react';

function DeviceMonitor() {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        const ws = new WebSocket('ws://localhost:8000/ws/stream');

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            setEvents(prev => [...prev, data].slice(-100));  // Keep last 100 events
        };

        return () => ws.close();
    }, []);

    return (
        <div>
            {events.map((event, i) => (
                <div key={i}>{event.type}: {JSON.stringify(event)}</div>
            ))}
        </div>
    );
}
```

### PyQt6 Integration

```python
from PyQt6.QtCore import QThread, pyqtSignal
import websockets
import json

class WebSocketThread(QThread):
    message_received = pyqtSignal(dict)

    async def connect(self):
        async with websockets.connect('ws://localhost:8000/ws/stream') as ws:
            async for message in ws:
                data = json.loads(message)
                self.message_received.emit(data)

    def run(self):
        import asyncio
        asyncio.run(self.connect())
```

## Connection Management

### Reconnection Logic

```javascript
class WebSocketClient {
    constructor(url) {
        this.url = url;
        this.reconnectDelay = 1000;
        this.connect();
    }

    connect() {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
            console.log('Connected');
            this.reconnectDelay = 1000;
        };

        this.ws.onmessage = (event) => {
            this.handleMessage(JSON.parse(event.data));
        };

        this.ws.onclose = () => {
            console.log('Disconnected, reconnecting...');
            setTimeout(() => this.connect(), this.reconnectDelay);
            this.reconnectDelay *= 2;  // Exponential backoff
        };
    }

    handleMessage(data) {
        // Handle message
    }
}
```

## Protocol Details

- **Endpoint:** `ws://localhost:8000/ws/stream` (or `wss://` for HTTPS)
- **Protocol:** WebSocket (RFC 6455)
- **Message Format:** JSON text messages
- **Heartbeat:** Not yet implemented (future feature)
- **Authentication:** Not yet implemented (future feature)

## Best Practices

1. **Handle reconnection** - Network may be unstable
2. **Parse messages safely** - Use try/catch for JSON parsing
3. **Rate limiting** - Don't overwhelm clients with too many events
4. **Filter events** - Client-side filtering for specific devices
5. **Buffer messages** - Handle bursts of events gracefully

## Troubleshooting

### Connection Refused

- Verify backend is running
- Check firewall rules
- Verify WebSocket port (default: 8000)

### Messages Not Received

- Check if discovery/monitoring are running
- Verify devices are being monitored
- Check browser console for errors

### Connection Drops Frequently

- Check network stability
- Implement reconnection logic
- Consider using a WebSocket proxy

## Security Considerations

- WebSocket endpoint currently has no authentication (future feature)
- Use WSS (WebSocket Secure) in production
- Implement rate limiting to prevent abuse
- Validate all incoming data on client side

## Future Enhancements

- Authentication/authorization
- Message filtering by device or event type
- Heartbeat/ping-pong for connection health
- Binary message format for efficiency
- Message history/replay capability

## Related Features

- [Discovery](20-discovery.md) - Triggers device_discovered events
- [Monitoring](22-monitoring.md) - Triggers latency and status events
- [API Reference](40-api-reference.md) - REST API documentation
