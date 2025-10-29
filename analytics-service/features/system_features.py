# analytics-service/features/system_features.py
from .base import BaseFeatureExtractor

class SystemFeatureExtractor(BaseFeatureExtractor):
    def extract(self, event):
        p = event.payload
        e = event.enrichment

        mem_used = (p.get("total_memory", 1) - p.get("available_memory", 0)) / (1024**3)
        mem_total = p.get("total_memory", 1) / (1024**3)
        mem_pct = (mem_used / mem_total) * 100 if mem_total > 0 else 0

        return {
            "cpu_usage": p.get("cpu_usage", 0),
            "memory_used_pct": round(mem_pct, 2),
            "disk_usage": p.get("disk_usage", 0),
            "uptime": p.get("uptime", 0),
            "high_cpu": p.get("cpu_usage", 0) > 80,
            "high_memory": mem_pct > 90,
            "threat_score": e.get("threat_score", 0)
        }