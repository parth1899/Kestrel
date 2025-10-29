# analytics-service/detectors/base.py
from abc import ABC, abstractmethod
from typing import Tuple, List, Dict

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, features: Dict, agent_id: str) -> Tuple[float, List[str]]:
        """Return (score, list_of_reasons)"""
        pass