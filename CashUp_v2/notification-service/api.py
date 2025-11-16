from fastapi import APIRouter, Body
from manager import NotificationManager, NotificationMessage

router = APIRouter()
manager = NotificationManager()

@router.post("/api/v1/notify/send")
async def send_notify(payload: dict = Body(...)):
    title = payload.get("title", "")
    content = payload.get("content", "")
    level = payload.get("level", "info")
    channels = payload.get("channels")
    msg = NotificationMessage(title, content, level, payload.get("metadata", {}))
    res = await manager.send(msg, channels)
    return {"code": 0, "message": "success", "data": res}