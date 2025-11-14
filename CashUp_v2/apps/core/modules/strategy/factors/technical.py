from typing import List, Dict, Any
from .base import FactorBase

class RSIFactor(FactorBase):
    def __init__(self, period: int = 14, overbought: float = 70.0, oversold: float = 30.0):
        super().__init__("rsi", {"period": period, "overbought": overbought, "oversold": oversold})

    def _rsi(self, closes: List[float], period: int) -> float:
        if len(closes) < period + 1:
            return 50.0
        gains = 0.0
        losses = 0.0
        for i in range(-period, -1):
            diff = closes[i+1] - closes[i]
            if diff > 0:
                gains += diff
            else:
                losses -= diff
        avg_gain = gains / period
        avg_loss = losses / period if losses > 0 else 0.000001
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def calculate(self, closes: List[float]) -> float:
        return self._rsi(closes, int(self.params["period"]))

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        rsi = self.calculate(closes)
        if rsi > float(self.params["overbought"]):
            return {"factor": self.name, "type": "sell", "strength": min(rsi/100.0, 1.0)}
        if rsi < float(self.params["oversold"]):
            return {"factor": self.name, "type": "buy", "strength": min((100.0-rsi)/100.0, 1.0)}
        return {"factor": self.name, "type": "none", "strength": 0.0}

class MAFactor(FactorBase):
    def __init__(self, period: int = 20):
        super().__init__("ma", {"period": period})

    def _ma(self, closes: List[float], period: int) -> float:
        if len(closes) < period:
            return sum(closes) / max(len(closes), 1)
        return sum(closes[-period:]) / period

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        ma = self._ma(closes, int(self.params["period"]))
        price = closes[-1] if closes else ma
        if price > ma:
            return {"factor": self.name, "type": "buy", "strength": 0.6}
        if price < ma:
            return {"factor": self.name, "type": "sell", "strength": 0.6}
        return {"factor": self.name, "type": "none", "strength": 0.0}

class EMAFactor(FactorBase):
    def __init__(self, period: int = 20):
        super().__init__("ema", {"period": period})

    def _ema(self, closes: List[float], period: int) -> float:
        if not closes:
            return 0.0
        k = 2 / (period + 1)
        ema = closes[0]
        for p in closes[1:]:
            ema = p * k + ema * (1 - k)
        return ema

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        ema = self._ema(closes, int(self.params["period"]))
        price = closes[-1] if closes else ema
        if price > ema:
            return {"factor": self.name, "type": "buy", "strength": 0.5}
        if price < ema:
            return {"factor": self.name, "type": "sell", "strength": 0.5}
        return {"factor": self.name, "type": "none", "strength": 0.0}