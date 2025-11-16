from typing import List, Dict, Any

class FactorBase:
    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params

    def calculate(self, closes: List[float]) -> float:
        return 0.0

    def get_signal(self, closes: List[float]) -> Dict[str, Any]:
        return {"factor": self.name, "type": "none", "strength": 0.0}