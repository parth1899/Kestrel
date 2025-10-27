# Kestrel – Endpoint Detection & Response (EDR)

**Kestrel** is an open, modular Endpoint Detection & Response (EDR) platform built around a microservices architecture.
It’s designed to provide real-time threat detection, enrichment, and automated containment across distributed systems.

> **Note:** Kestrel is under active development. This repository currently includes early-stage components and service scaffolds.

---

## Overview

Current components
* **Windows Telemetry Agent** - lightweight agent for Windows hosts
* **Threat Intelligence Enrichment Service** - service for IOC lookups, YARA scans & enrichment

Additional components (in progress):

* **Real-time Analytics (Streaming)** – consumes enriched events, performs anomaly detection, and emits alerts.
* **Containment Playbook Engine** – executes YAML-driven response actions (e.g., isolate host, kill process).
* **Backend (Management Plane)** – FastAPI-based control plane for users, inventory, and audit logs.
* **Decision Engine** – cost-aware policy evaluation using OPA or internal logic.

---