# utils/model_loader.py
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"

def load_model(event_type: str):
    path = MODEL_DIR / f"isolation_forest_{event_type}.pkl"
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}")
    return joblib.load(path)