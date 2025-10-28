from abc import ABC, abstractmethod
from typing import Dict
from core.models import EnrichedEvent

class BaseFeatureExtractor(ABC):
    @abstractmethod
    def extract(self, event: EnrichedEvent) -> Dict:
        pass