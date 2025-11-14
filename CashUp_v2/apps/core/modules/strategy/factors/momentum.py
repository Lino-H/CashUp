from typing import List, Dict, Any
from .base import FactorBase

class MACDFactor(FactorBase):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("macd", {"fast": fast, "slow": slow, "signal": signal})

    def _ema(self, closes: List[float], period: int) -> float:
        if not closes:
            return 0.0
        k = 2 / (period + 1)
        ema = closes[0]
        for p in closes[1:]:
            ema = p * k + ema * (1 - k)
        return ema

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        f = int(self.params["fast"])
        s = int(self.params["slow"])
        sig = int(self.params["signal"])
        if len(closes) < s + sig:
            return {"factor": self.name, "type": "none", "strength": 0.0}
        macd_line = self._ema(closes[-s:], f) - self._ema(closes[-s:], s)
        signal_line = self._ema([macd_line] * sig, sig)
        if macd_line > signal_line:
            return {"factor": self.name, "type": "buy", "strength": 0.5}
        if macd_line < signal_line:
            return {"factor": self.name, "type": "sell", "strength": 0.5}
        return {"factor": self.name, "type": "none", "strength": 0.0}