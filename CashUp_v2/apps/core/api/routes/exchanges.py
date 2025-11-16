from fastapi import APIRouter
import os
import yaml

router = APIRouter()

@router.get("/api/v1/exchanges")
async def list_exchanges():
    path = os.path.join(os.getcwd(), "configs", "exchanges.yaml")
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except Exception:
        cfg = {}
    names = [k for k in cfg.keys() if k not in ("common", "risk_control", "monitoring")]
    return {"code": 0, "message": "success", "data": names}