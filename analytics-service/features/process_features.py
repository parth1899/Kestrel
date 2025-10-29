from .base import BaseFeatureExtractor
from utils.cache import incr_counter

class ProcessFeatureExtractor(BaseFeatureExtractor):
    def extract(self, event):
        p = event.payload
        e = event.enrichment
        agent = event.agent_id

        # Stateful: process start frequency
        freq_key = f"proc:{p.get('process_name', 'unknown')}"
        freq = incr_counter(agent, freq_key)

        return {
            "process_name": p.get("process_name", ""),
            "command_line_len": len(p.get("command_line", "")),
            "is_system_parent": p.get("parent_process_id") == 0,
            "vt_positives": e.get("reputation", {}).get("vt", {}).get("positives", 0),
            "hash_known_malicious": e.get("reputation", {}).get("vt", {}).get("positives", 0) > 10,
            "yara_hits_count": len(e.get("yara_hits", [])),
            "threat_score": e.get("threat_score", 0),
            "proc_freq_per_hour": freq,
            "is_suspicious_path": "temp" in p.get("executable_path", "").lower()
        }