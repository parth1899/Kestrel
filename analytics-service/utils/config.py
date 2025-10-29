# analytics-service/utils/config.py
import yaml
from pathlib import Path

def load_config() -> dict:
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)