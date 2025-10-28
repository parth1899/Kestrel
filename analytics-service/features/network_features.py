# analytics-service/features/network_features.py
from .base import BaseFeatureExtractor

class NetworkFeatureExtractor(BaseFeatureExtractor):
    def extract(self, event):
        p = event.payload
        e = event.enrichment

        remote_ip = p.get("remote_ip", "")
        local_ip = p.get("local_ip", "")

        return {
            "remote_ip": remote_ip,
            "local_ip": local_ip,
            "remote_port": p.get("remote_port", 0),
            "bytes_sent": p.get("bytes_sent", 0),
            "bytes_received": p.get("bytes_received", 0),
            "protocol": p.get("protocol", ""),
            "is_loopback": remote_ip in ["127.0.0.1", "::1", "0.0.0.0"],
            "is_private_ip": remote_ip.startswith("192.168.") or remote_ip.startswith("10."),
            "otx_pulses": e["reputation"].get("otx", {}).get("pulses", 0),
            "geoip_country": e["geoip"].get("country", ""),
            "threat_score": e.get("threat_score", 0)
        }