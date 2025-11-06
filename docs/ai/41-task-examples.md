# Task Automation Examples

## Overview

Common automation tasks for Network Device Monitor using Python scripts and API calls.

## Discovery Automation

### Scheduled Discovery Scan

```python
"""
Automated network discovery that runs periodically.
"""
import asyncio
import httpx
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def scheduled_discovery():
    """Run discovery scan and log results."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/discovery/scan",
            json={
                "cidr": "192.168.1.0/24",
                "persist": True,
                "identify": True
            },
            timeout=60.0
        )
        result = response.json()
        print(f"[{datetime.now()}] Discovered {result['count']} devices")
        return result

# Run every hour
if __name__ == "__main__":
    while True:
        asyncio.run(scheduled_discovery())
        asyncio.sleep(3600)  # 1 hour
```

### Discovery with Notifications

```python
"""
Run discovery and send notifications for new devices.
"""
import asyncio
import httpx
import smtplib
from email.message import EmailMessage

async def discover_and_notify():
    # Get existing devices
    async with httpx.AsyncClient() as client:
        existing = await client.get(f"{BASE_URL}/api/devices")
        existing_ips = {d['ip'] for d in existing.json() if d.get('ip')}

        # Run discovery
        scan = await client.post(
            f"{BASE_URL}/api/discovery/scan",
            json={"persist": True, "identify": True}
        )
        result = scan.json()

        # Find new devices
        new_devices = [
            d for d in result['devices']
            if d.get('ip') and d['ip'] not in existing_ips
        ]

        # Send notification if new devices found
        if new_devices:
            send_email_notification(new_devices)
            print(f"Found {len(new_devices)} new devices!")

def send_email_notification(devices):
    msg = EmailMessage()
    msg['Subject'] = f'Network Alert: {len(devices)} New Devices'
    msg['From'] = 'monitor@example.com'
    msg['To'] = 'admin@example.com'

    body = "New devices discovered:\\n\\n"
    for d in devices:
        body += f"- {d.get('ip')} ({d.get('vendor', 'Unknown')})\\n"
    msg.set_content(body)

    # Send email (configure SMTP settings)
    # with smtplib.SMTP('localhost') as s:
    #     s.send_message(msg)
```

## Monitoring Automation

### Batch Device Monitoring

```python
"""
Monitor all devices and generate reports.
"""
import asyncio
import httpx
from datetime import datetime
import csv

async def monitor_all_devices():
    """Monitor all devices and save results to CSV."""
    async with httpx.AsyncClient() as client:
        # Get device list
        response = await client.get(f"{BASE_URL}/api/devices")
        devices = response.json()

        results = []
        for device in devices:
            if not device.get('ip'):
                continue

            # Get metrics
            try:
                metrics = await client.get(
                    f"{BASE_URL}/api/metrics/latency",
                    params={
                        "device_id": device['id'],
                        "start": "-5m",
                        "limit": 1
                    }
                )
                latest = metrics.json()
                if latest:
                    results.append({
                        'timestamp': datetime.now().isoformat(),
                        'ip': device['ip'],
                        'hostname': device.get('hostname', 'N/A'),
                        'latency_ms': latest[0].get('ms'),
                        'packet_loss': latest[0].get('loss'),
                        'status': device.get('status', 'unknown')
                    })
            except Exception as e:
                print(f"Error monitoring {device['ip']}: {e}")

        # Save to CSV
        if results:
            with open(f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 'w') as f:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

        return results

if __name__ == "__main__":
    results = asyncio.run(monitor_all_devices())
    print(f"Monitored {len(results)} devices")
```

### Alert on High Latency

```python
"""
Monitor devices and send alerts for high latency.
"""
import asyncio
import httpx

LATENCY_THRESHOLD_MS = 200.0
PACKET_LOSS_THRESHOLD = 0.1

async def check_alerts():
    async with httpx.AsyncClient() as client:
        devices = (await client.get(f"{BASE_URL}/api/devices")).json()

        alerts = []
        for device in devices:
            if not device.get('ip'):
                continue

            metrics = await client.get(
                f"{BASE_URL}/api/metrics/latency",
                params={"device_id": device['id'], "start": "-5m", "limit": 5}
            )
            points = metrics.json()

            if not points:
                continue

            # Check thresholds
            avg_latency = sum(p['ms'] for p in points) / len(points)
            avg_loss = sum(p['loss'] for p in points) / len(points)

            if avg_latency > LATENCY_THRESHOLD_MS:
                alerts.append(f"HIGH LATENCY: {device['ip']} ({device.get('hostname', 'N/A')}): {avg_latency:.1f}ms")

            if avg_loss > PACKET_LOSS_THRESHOLD:
                alerts.append(f"PACKET LOSS: {device['ip']} ({device.get('hostname', 'N/A')}): {avg_loss*100:.1f}%")

        if alerts:
            print("\\n".join(alerts))
            # Send alerts via email, webhook, etc.

        return alerts
```

## Data Export

### Export Device Inventory

```python
"""
Export device inventory to JSON/CSV formats.
"""
import asyncio
import httpx
import json
import csv

async def export_inventory(format='json'):
    async with httpx.AsyncClient() as client:
        devices = (await client.get(f"{BASE_URL}/api/devices")).json()

        if format == 'json':
            with open('device_inventory.json', 'w') as f:
                json.dump(devices, f, indent=2)
        elif format == 'csv':
            if devices:
                keys = ['id', 'ip', 'mac', 'hostname', 'vendor', 'device_type', 'status']
                with open('device_inventory.csv', 'w') as f:
                    writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(devices)

        print(f"Exported {len(devices)} devices to {format.upper()}")

if __name__ == "__main__":
    asyncio.run(export_inventory('csv'))
```

### Metrics Data Export

```python
"""
Export historical metrics to CSV for analysis.
"""
import asyncio
import httpx
import csv
from datetime import datetime

async def export_metrics(device_id, start="-24h", output_file=None):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/api/metrics/latency",
            params={
                "device_id": device_id,
                "start": start,
                "limit": 1000
            }
        )
        metrics = response.json()

        if not output_file:
            output_file = f"metrics_{device_id}_{datetime.now().strftime('%Y%m%d')}.csv"

        with open(output_file, 'w') as f:
            if metrics:
                writer = csv.DictWriter(f, fieldnames=['ts', 'ms', 'loss'])
                writer.writeheader()
                writer.writerows(metrics)

        print(f"Exported {len(metrics)} metric points to {output_file}")

if __name__ == "__main__":
    asyncio.run(export_metrics("192.168.1.1", start="-7d"))
```

## Integration Scripts

### Webhook Integration

```python
"""
Send webhook notifications for device events.
"""
import asyncio
import httpx
import websockets
import json

WEBHOOK_URL = "https://your-webhook-endpoint.com/notify"

async def stream_and_notify():
    """Connect to WebSocket and forward events to webhook."""
    async with websockets.connect("ws://localhost:8000/ws/stream") as ws:
        async for message in ws:
            data = json.loads(message)

            # Forward specific events to webhook
            if data['type'] in ['device_discovered', 'device_down']:
                async with httpx.AsyncClient() as client:
                    await client.post(WEBHOOK_URL, json=data)
                print(f"Forwarded {data['type']} event to webhook")
```

### Slack Integration

```python
"""
Send Slack notifications for network events.
"""
import asyncio
import httpx

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

async def send_slack_alert(message):
    async with httpx.AsyncClient() as client:
        await client.post(
            SLACK_WEBHOOK,
            json={"text": message}
        )

async def monitor_and_alert():
    async with httpx.AsyncClient() as client:
        devices = (await client.get(f"{BASE_URL}/api/devices")).json()

        for device in devices:
            if device.get('status') == 'down':
                await send_slack_alert(
                    f":warning: Device DOWN: {device.get('hostname', device['ip'])}"
                )
```

## Batch Operations

### Bulk Discovery Multiple Networks

```python
"""
Discover multiple network segments.
"""
import asyncio
import httpx

NETWORKS = [
    "192.168.1.0/24",
    "192.168.2.0/24",
    "10.0.0.0/24"
]

async def discover_all_networks():
    async with httpx.AsyncClient(timeout=120.0) as client:
        tasks = [
            client.post(
                f"{BASE_URL}/api/discovery/scan",
                json={"cidr": cidr, "persist": True, "identify": True}
            )
            for cidr in NETWORKS
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_devices = 0
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error scanning {NETWORKS[i]}: {result}")
            else:
                data = result.json()
                total_devices += data['count']
                print(f"{NETWORKS[i]}: {data['count']} devices")

        print(f"\\nTotal: {total_devices} devices across {len(NETWORKS)} networks")

if __name__ == "__main__":
    asyncio.run(discover_all_networks())
```

## Scheduled Tasks with APScheduler

```python
"""
Production-grade scheduled tasks using APScheduler.
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

scheduler = AsyncIOScheduler()

async def hourly_discovery():
    # Discovery task
    pass

async def daily_report():
    # Generate daily report
    pass

async def realtime_monitoring():
    # Continuous monitoring
    pass

# Schedule tasks
scheduler.add_job(hourly_discovery, CronTrigger(minute=0))  # Every hour
scheduler.add_job(daily_report, CronTrigger(hour=8, minute=0))  # Daily at 8 AM
scheduler.add_job(realtime_monitoring, 'interval', seconds=60)  # Every minute

scheduler.start()

# Keep alive
asyncio.get_event_loop().run_forever()
```
