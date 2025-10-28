# analytics-service/features/__init__.py
from .file_features import FileFeatureExtractor
from .network_features import NetworkFeatureExtractor
from .process_features import ProcessFeatureExtractor
from .system_features import SystemFeatureExtractor

def get_extractor(event_type: str):
    mapping = {
        "file": FileFeatureExtractor(),
        "network": NetworkFeatureExtractor(),
        "process": ProcessFeatureExtractor(),
        "system": SystemFeatureExtractor(),
    }
    return mapping.get(event_type, ProcessFeatureExtractor())  # fallback