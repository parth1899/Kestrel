# detectors/rule_based.py
class RuleBasedDetector:
    def __init__(self):
        self.rules = [
            # 1. High threat score
            lambda f: f.get("threat_score", 0) >= 80,

            # 2. Known malicious hash (VT positives > 10)
            lambda f: f.get("vt_positives", 0) > 10,

            # 3. Multiple YARA hits
            lambda f: f.get("yara_hits_count", 0) >= 2,

            # 4. System parent + high frequency
            lambda f: f.get("is_system_parent", False) and f.get("proc_freq_per_hour", 0) > 5,

            # 5. Suspicious path
            lambda f: f.get("is_suspicious_path", False),
        ]

    def detect(self, features: dict):
        score = 0.0
        reasons = []
        for i, rule in enumerate(self.rules):
            try:
                if rule(features):
                    score += 20
                    reasons.append(f"rule_{i+1}")
            except:
                pass  # never crash
        return min(score, 100), reasons