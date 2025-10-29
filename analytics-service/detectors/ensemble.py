# analytics-service/detectors/ensemble.py
from .rule_based import RuleBasedDetector
from .anomaly import AnomalyDetector
from .behavioral import BehavioralDetector

class EnsembleDetector:
    def __init__(self, weights=None):
        self.weights = weights or {"rule": 0.4, "anomaly": 0.3, "behavioral": 0.3}
        self.rule = RuleBasedDetector()
        self.anomaly = AnomalyDetector()
        self.behavioral = BehavioralDetector()

    def detect(self, features: dict, agent_id: str, event_type: str):
        r_score, r_reasons = self.rule.detect(features)
        a_score, a_reasons = self.anomaly.detect(features, event_type)
        b_score, b_reasons = self.behavioral.detect(features, agent_id, event_type)

        total = (
            r_score * self.weights["rule"] +
            a_score * self.weights["anomaly"] +
            b_score * self.weights["behavioral"]
        )

        reasons = {
            "rule": r_reasons,
            "anomaly": a_reasons,
            "behavioral": b_reasons
        }
        return round(total, 2), reasons