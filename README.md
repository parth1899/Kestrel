# Kestrel – AI-Driven Endpoint Detection & Response (EDR)

**Kestrel** is an intelligent, real-time endpoint security platform designed for hybrid (cloud + on-prem) environments. It combines behavioral analytics, AI-driven anomaly detection, and policy-based automated response to detect both known and unknown threats.

---

## The Problem

Traditional endpoint security tools were designed for static, on-premises environments and signature-based threats. They struggle with:

- **Fragmented Visibility** – Cloud VMs, containers, and on-prem servers are monitored by separate tools
- **Novel & Low-and-Slow Attacks** – Static rules and signatures don't adapt to evolving attacker behaviors
- **Alert Fatigue** – Security teams are overwhelmed, slowing incident response

## Our Solution

Kestrel delivers faster incident detection, reduced manual effort, and cost-effective protection through:

- High-fidelity telemetry collection from agents and cloud APIs
- Behavioral learning to establish baselines and flag anomalies
- Automated remediation via policy-driven playbooks
- Unified visibility across hybrid infrastructure

---

## Architecture

Kestrel follows a modular microservices architecture with four key layers:

| Layer | Components |
|-------|------------|
| **Data Plane** | Windows Agent, Telemetry Collectors |
| **Processing Pipeline** | Threat Enrichment Service, Real-time Analytics |
| **Decision & Response** | Decision Engine, Playbook Engine |
| **Management & Observability** | Management Plane (FastAPI), Frontend Dashboard, Grafana |

### Components

| Component | Description |
|-----------|-------------|
| **Windows Agent** | Lightweight Go-based agent collecting process, network, and file events |
| **Threat Enrichment Service** | IOC lookups (VirusTotal), YARA scanning, GeoIP enrichment |
| **Analytics Service** | ML-based anomaly detection, behavioral analysis, rule-based alerting |
| **Playbook Engine** | YAML-driven automated response actions (isolate host, kill process, quarantine) |
| **Management Plane** | FastAPI backend for policy management, inventory, and audit logs |
| **Frontend** | React/TypeScript dashboard for security operations |
| **Grafana Dashboards** | Pre-built dashboards for threat overview, network/file/process activity |

---

## Data Flow

Events flow through a real-time pipeline orchestrated by RabbitMQ:

<img width="1810" height="483" alt="image" src="https://github.com/user-attachments/assets/5a2250d4-643a-406f-8e67-4fa13138d423" />

### Pipeline Example

**1. Raw Event** (Windows Agent)
```json
{
  "event_id": "e3612ac8-33f4-6fd4-dbae-c8faf5ebccf9",
  "agent_id": "windows-agent-001",
  "event_type": "process",
  "payload": {
    "process_name": "mimikatz.exe",
    "executable_path": "C:\\Users\\parth\\AppData\\Local\\Temp\\mimikatz.exe",
    "hash": "61C0810A23580CF492A6BA4F7654566108331E7A4134C968C2D6A05261B2D8A1",
    "process_id": 9680,
    "username": "PARTHS-LAPTOP\\parth"
  },
  "timestamp": "2025-12-04T14:44:48+05:30"
}
```

**2. Enriched Event** (Threat Enrichment Service)
```json
{
  "event_id": "e3612ac8-33f4-6fd4-dbae-c8faf5ebccf9",
  "enrichment": {
    "ioc_matches": ["vt_process_malicious"],
    "reputation": {
      "vt": { "positives": 66, "total": 76 }
    },
    "yara_hits": ["Suspicious_File_Extension", "Suspicious_Executable_In_UserDir"],
    "threat_score": 85.0
  }
}
```

**3. Alert** (Analytics Service)
```json
{
  "id": "2d1f8ab9-ed1a-4ca4-9ed8-24907658eeb4",
  "event_id": "e3612ac8-33f4-6fd4-dbae-c8faf5ebccf9",
  "score": 60.77,
  "severity": "medium",
  "details": {
    "features": {
      "vt_positives": 66,
      "hash_known_malicious": true,
      "yara_hits_count": 2,
      "is_suspicious_path": true
    },
    "reasons": {
      "rule": ["rule_1", "rule_2", "rule_3", "rule_5"],
      "anomaly": ["anomaly_high"]
    },
    "model": "ensemble"
  }
}
```

---

## Repository Structure

```
kestrel/
├── windows-agent/        # Go-based telemetry agent for Windows
├── threat-enrichment/    # IOC lookup, YARA scanning, GeoIP enrichment
├── analytics-service/    # ML anomaly detection & alerting
├── playbook-engine/      # Automated response orchestration
├── management-plane/     # FastAPI backend & control plane
├── frontend/             # React/TypeScript dashboard
├── grafana/              # Pre-configured dashboards & provisioning
└── docs/                 # Documentation
```

---

## Getting Started

Each component includes its own Dockerfile and configuration. See individual component READMEs for setup instructions:

- [Windows Agent](./windows-agent/)
- [Threat Enrichment Service](./threat-enrichment/README.md)
- [Management Plane](./management-plane/README.md)
- [Grafana Setup](./docs/Grafana-Setup.md)

### Prerequisites

- Docker & Docker Compose
- RabbitMQ
- PostgreSQL
- Go 1.21+ (for Windows Agent)
- Python 3.11+ (for backend services)
- Node.js 18+ (for frontend)

---

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.
