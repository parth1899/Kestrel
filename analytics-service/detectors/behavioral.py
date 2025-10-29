# detectors/behavioral.py
from river import anomaly, preprocessing
from utils.cache import get_counter

class BehavioralDetector:
    def __init__(self):
        self.models = {}

    def get_model(self, agent_id, event_type):
        key = f"{agent_id}:{event_type}"
        if key not in self.models:
            model = (
                preprocessing.StandardScaler() |
                anomaly.QuantileFilter(anomaly.HalfSpaceTrees(), q=0.95)
            )
            self.models[key] = model
        return self.models[key]

    def detect(self, features: dict, agent_id: str, event_type: str) -> tuple[float, list]:
        model = self.get_model(agent_id, event_type)

        # === EVENT-TYPE SPECIFIC FEATURES ===
        if event_type == "process":
            x = {
                "cmd_len": features.get("command_line_len", 0),
                "freq": features.get("proc_freq_per_hour", 0)
            }
        elif event_type == "file":
            x = {
                "size": features.get("file_size", 0),
                "freq": features.get("temp_file_freq", 0),
                "yara": features.get("yara_hits_count", 0)
            }
        elif event_type == "network":
            x = {
                "bytes": features.get("bytes_sent", 0) + features.get("bytes_received", 0),
                "port": features.get("remote_port", 0)
            }
        elif event_type == "system":
            x = {
                "cpu": features.get("cpu_usage", 0),
                "mem": features.get("memory_used_pct", 0),
                "disk": features.get("disk_usage", 0)
            }
        else:
            return 0.0, []

        if not x:
            return 0.0, []

        score = model.score_one(x)
        model.learn_one(x)
        return (min(score * 100, 100), ["behavioral_outlier"]) if score > 0.8 else (0.0, [])