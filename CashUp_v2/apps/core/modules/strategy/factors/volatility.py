from typing import List, Dict, Any
from .base import FactorBase

class BollingerFactor(FactorBase):
    def __init__(self, period: int = 20, mult: float = 2.0):
        super().__init__("boll", {"period": period, "mult": mult})

    def _sma(self, closes: List[float], period: int) -> float:
        if len(closes) < period:
            return sum(closes) / max(len(closes), 1)
        return sum(closes[-period:]) / period

    def _std(self, closes: List[float], period: int) -> float:
        if len(closes) < period:
            return 0.0
        window = closes[-period:]
        m = sum(window) / period
        v = sum((x - m) ** 2 for x in window) / period
        return v ** 0.5

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        p = int(self.params["period"]) 
        m = float(self.params["mult"]) 
        sma = self._sma(closes, p)
        std = self._std(closes, p)
        upper = sma + m * std
        lower = sma - m * std
        price = closes[-1] if closes else sma
        if price > upper:
            return {"factor": self.name, "type": "sell", "strength": 0.6}
        if price < lower:
            return {"factor": self.name, "type": "buy", "strength": 0.6}
        return {"factor": self.name, "type": "none", "strength": 0.0}

class ATRFactor(FactorBase):
    def __init__(self, period: int = 14):
        super().__init__("atr", {"period": period})

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        return {"factor": self.name, "type": "none", "strength": 0.0}