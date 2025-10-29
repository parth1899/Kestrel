# detectors/anomaly.py
import joblib
from utils.model_loader import load_model
import numpy as np

class AnomalyDetector:
    def detect(self, features: dict, event_type: str = "process"):
        model = load_model(event_type)
        numeric_feats = [v for v in features.values() if isinstance(v, (int, float, bool))]
        if not numeric_feats:
            return 0.0, []

        X = np.array([numeric_feats], dtype=np.float32)
        score = model.decision_function(X)[0]
        pred = model.predict(X)[0]

        if pred == -1:
            anomaly_score = max(0, min(100, 100 + score * 100))
            return anomaly_score, ["anomaly_high"]
        return 0.0, []