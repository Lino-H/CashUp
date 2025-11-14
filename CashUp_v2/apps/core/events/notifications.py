import os
import httpx

async def publish(event_type: str, data: dict):
    base = os.getenv("NOTIFICATION_URL", "http://localhost:8004")
    url = f"{base}/api/v1/notify/send"
    title = event_type
    content = str(data)
    payload = {"title": title, "content": content, "level": "info"}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json=payload)
    except Exception:
        return False
    return True