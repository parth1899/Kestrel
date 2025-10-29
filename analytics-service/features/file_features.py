# analytics-service/features/file_features.py
from .base import BaseFeatureExtractor
from utils.cache import incr_counter

class FileFeatureExtractor(BaseFeatureExtractor):
    def extract(self, event):
        p = event.payload
        e = event.enrichment
        agent = event.agent_id

        file_path = p.get("file_path", "").lower()
        file_name = p.get("file_name", "").lower()

        # Stateful: count temp file creations
        temp_count = incr_counter(agent, "file:temp_create")

        return {
            "file_name": file_name,
            "file_ext": p.get("file_type", ""),
            "file_size": p.get("file_size", 0),
            "is_temp_dir": any(x in file_path for x in ["temp", "tmp", "appdata/local/temp"]),
            "is_script": p.get("file_type") in [".ps1", ".vbs", ".js", ".bat", ".cmd"],
            "yara_hits": len(e.get("yara_hits", [])),
            "otx_pulses": e["reputation"].get("otx", {}).get("pulses", 0),
            "vt_positives": e["reputation"].get("vt", {}).get("positives", 0),
            "threat_score": e.get("threat_score", 0),
            "temp_file_freq": temp_count
        }