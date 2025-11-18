# Kestrel Playbook Engine – Complete Context Guide

This document gives a compact but complete overview of the Kestrel Playbook Engine and how it fits into the broader repository. You can hand this to another LLM as context to reason about the system, generate code, or debug issues.

## Top-level repository structure

- analytics-service/ — Python analytics and anomaly detection (features, detectors, alerting)
- management-plane/ — FastAPI service for CRUD and orchestration (policies, rules, alerts, users)
- playbook-engine/ — FastAPI service that generates and executes remediation playbooks (this doc deep-dives here)
- threat-enrichment/ — Enrichment service (YARA, external lookups), Dockerized
- frontend/ — Vite + React UI (TypeScript)
- grafana/ — Dashboards + provisioning
- windows-agent/ — Go-based endpoint agent (collectors, services); not required by the Playbook Engine in local mode
- docs/ — General docs (Overview, RepoStructure)

## What the Playbook Engine does

The Playbook Engine turns alerts into executable playbooks. It can:

- Generate a YAML playbook from an alert using an LLM (Groq, OpenAI, Anthropic) or a deterministic fallback.
- Parse and validate the YAML against an actions schema.
- Execute actions locally on the host (Windows-first today):
  - quarantine_file — move file into quarantine directory
  - kill_process — taskkill by PID
  - block_ip — add Windows firewall rules via netsh
  - isolate_host — placeholder (admin required; default disabled)
- Persist results (JSON per execution) or keep in-memory only (toggleable).
- Log audit events to a JSONL file.

Works standalone (no agent HTTP calls). Messaging (RabbitMQ) and Redis are optional.

## Runtime architecture (playbook-engine)

- src/main.py — FastAPI app (health, API routers), startup hooks (optional message/file ingestion)
- src/api/
  - playbooks.py — REST endpoints to generate playbooks and fetch by id
  - executions.py — REST endpoint to run a playbook + fetch results
- src/genai/
  - prompts.py — Builds prompt from alert and actions schema
  - generator.py — Calls provider (Groq/OpenAI/Anthropic) or fallback; normalizes YAML; writes generated files to top-level `playbooks/` directory (was `data/playbooks/generated`)
- src/core/
  - parser.py — Pydantic models + YAML parsing + validation against actions schema
  - evaluator.py — Simple preconditions (equals/contains)
  - executor.py — Runs steps sequentially, handles rollback, writes results, emits audit
- src/actions/
  - registry.py — Local action implementations + rollbacks (Windows-first)
- src/messaging/
  - consumer.py — Optional RabbitMQ or single-file ingestion of alerts
- src/utils/
  - config.py — Load/merge config (file + env), expose toggles, ensure data dirs
  - logger.py — App logger + audit.jsonl writer
  - redis_client.py — Optional Redis locks + cooldown with graceful degradation

Data/config layout (within playbook-engine/):

- config/config.yaml — primary config (RabbitMQ URL, Redis URL/TTL, GenAI provider/model/key, etc.)
- config/actions.yaml — declares actions and required params for schema validation
Directories summary:
data/playbooks/static
- Checked-in canonical playbooks (if any)
data/playbooks/generated
- Generated YAML playbooks (LLM or fallback)
data/executions
- Execution result JSON files (if EXECUTIONS_PERSIST=true) or absent if disabled
data/quarantine
- Quarantined files
data/audit.jsonl
- Append-only audit log
- logs/app.log — rotating text logs

## Key configuration toggles

Environment variables override config.yaml via src/utils/config.py.

- Execution mode and persistence
  - EXECUTION_MODE=local (default)
  - EXECUTIONS_PERSIST=true|false (default true); if false, results are stored in-memory
  - QUARANTINE_DIR (default data/quarantine)
  - ALLOW_ISOLATE_HOST=true|false (default false)
- Redis (optional)
  - REDIS_URL
  - REDIS_COOLDOWN_ENABLED=true|false (default true)
  - REDIS_COOLDOWN_TTL=seconds (default 300; repo config may set 5 for testing)
- GenAI provider config
  - GENAI_PROVIDER=openai|anthropic|groq|stub (default openai)
  - GENAI_MODEL (e.g., llama-3.1-8b-instant)
  - GROQ_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
- Messaging (optional)
  - RABBITMQ_URL, RABBITMQ_EXCHANGE, FILE_INPUT_PATH

All directories under data/ are created on startup if missing.

## Playbook model (YAML)

Required shape, enforced by Pydantic + actions schema:

```yaml
id: pb-<event_type>-<severity>
version: "1.0"
metadata:
  event_type: file|process|network
  severity: low|medium|high|critical
preconditions: []               # optional
steps:
  - name: <human title>
    action: quarantine_file|kill_process|block_ip|isolate_host
    params: { key: value }      # must include required params per actions.yaml
    on_error: stop|continue     # optional (default stop)
rollback: []                    # optional steps, same shape as steps
```

If the LLM emits invalid YAML (e.g., missing name/action fields, numeric version), the engine logs a warning and falls back to a deterministic YAML that matches the schema.

## Local actions (Windows)

- quarantine_file
  - Moves path to data/quarantine/`hashed-suffix`.quar
  - Rollback: moves it back (best-effort)
- kill_process
  - Runs: `taskkill /PID <pid> /F`
  - Idempotent: if process not found, returns status=already_terminated
  - Rollback: noop (cannot resurrect processes)
- block_ip (Admin required)
  - Adds inbound/outbound block rules with netsh
  - Rollback: removes those rules by name
- isolate_host (Admin required)
  - Placeholder: currently not enabled by default; intended to block all in/out traffic

## REST API (FastAPI)

- GET /health — simple health check
- POST /api/playbooks/generate — body: alert JSON
  - Generates and stores a YAML file under data/playbooks/generated
- GET /api/playbooks/{playbook_id}
  - Fetches YAML by id from static or generated directories
- POST /api/executions/run — body: { playbook_id, alert }
  - Executes the playbook against the alert; returns an ExecutionResult JSON
- GET /api/executions/{execution_id}
  - Returns stored JSON result (or, if persistence disabled, looks in in-memory cache)

See `playbook-engine/requests.rest` for concrete examples (VS Code REST Client).

## Audit & execution logging

- Audit: `data/audit.jsonl` — JSON line per event with fields `{ ts, event, ... }`, e.g. playbook_generated, execution_started, step_executed, execution_completed
- Execution results:
  - If EXECUTIONS_PERSIST=true: `data/executions/<uuid>.json`
  - If false: kept in memory; retrievable while the process is running

## Redis usage (optional, safe to disable)

- acquire_lock: prevents concurrent conflicting executions per agent/event key
- check_and_set_cooldown: suppresses thrashing for repeated alerts of same type/severity
- If Redis is unavailable or auth fails, both features degrade gracefully (warnings are logged; execution proceeds)

## LLM providers and fallback behavior

- Provider is selected by GENAI_PROVIDER; if the corresponding API key is missing, the engine uses a deterministic fallback.
- If provider returns invalid YAML, engine validates and then falls back automatically.
- Prompt is constructed from the alert JSON and actions schema (see src/genai/prompts.py).

Note: If you want to preserve LLM-provided content but fix only structural issues, add a transformation pass before validation (e.g., convert `- quarantine_file: {path: ...}` into the canonical list-of-objects with `name`, `action`, `params`). Currently, the engine uses a strict fallback for reliability.

## Tests

- Unit:
  - tests/test_parser.py — YAML parsing/validation
  - tests/test_executor.py — quarantine action flow
- End-to-end (real OS actions + real LLM if key present):
  - tests/test_e2e_end_to_end.py
    - File: quarantines a temp file
    - Process: starts notepad and kills by PID (idempotent)
    - Network: blocks a test IP (skipped without admin)
  - Tests disable cooldown and persistence to reduce flakiness.

Run tests (Windows, PowerShell):

```powershell
# In playbook-engine/
$env:GROQ_API_KEY = '<key>'  # optional; otherwise tests using Groq are skipped
pytest -q
```

## How to run the engine locally

```powershell
# From playbook-engine/
# Optionally disable cooldown/persistence while testing:
$env:REDIS_COOLDOWN_ENABLED = 'false'
$env:EXECUTIONS_PERSIST = 'false'

# Start API
.\nvenv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 9000
```

Try with REST Client (see `requests.rest`) or curl.

## Troubleshooting

- 500 Under cooldown: Disable via `REDIS_COOLDOWN_ENABLED=false` or wait TTL.
- Redis auth/availability: The engine degrades gracefully; check logs for warnings.
- netsh permission denied: Run as Administrator or skip block_ip/isolate_host.
- Windows path escaping: Prefer forward slashes in JSON/YAML (`C:/Temp/file.bin`).
- Execution JSON files are created by default: set `EXECUTIONS_PERSIST=false` to avoid on-disk writes.

## Security & safety notes

- Local actions run on the host. Review playbooks before executing in production.
- `isolate_host` and `block_ip` require Admin and can be disruptive; keep opt-in.
- Quarantine moves files; ensure the quarantine directory is secured.

---

If you need a black-box API test harness or a YAML transformation pass to auto-fix LLM outputs, ask for the “API E2E module” or the “LLM YAML normalizer” and I can add it.

## Feature Matrix

Core Execution & Modeling:
- Alert -> Playbook generation (LLM providers: Groq, OpenAI, Anthropic; stub deterministic fallback).
- YAML normalization pass (_normalize_yaml_to_schema) fixing common LLM structural issues (single-key step mappings, missing params, numeric versions).
- Pydantic schema enforcement (Step, Playbook) + actions.yaml param validation.
- Deterministic playbook ID normalization (pb-<event_type>-<severity>) for reliable lookup.
- Preconditions engine supporting:
  - equals/contains operators
  - Plain key:value dict fallback (event_type, severity, agent_id) after LLM output.
- Sequential step execution with on_error policies (stop | continue).
- Rollback support (reverse order, registered rollback handlers, graceful skip if absent).
- Local Windows-centric actions: quarantine_file, kill_process, block_ip, isolate_host (skipped if not admin or not allowed).
- Idempotent action behavior (taskkill already terminated, firewall rules removed before add, quarantine path hashing).
- Skip logic for isolate_host if ALLOW_ISOLATE_HOST=false or non-admin.

Persistence & State:
- Optional execution result persistence (EXECUTIONS_PERSIST=true) -> data/executions JSON; in-memory otherwise.
- Audit trail (data/audit.jsonl) for generation, start, steps, errors, rollbacks, completion.
- Redis (optional) cooldown (event_type:severity key) & execution lock (agent_id:event_id) with graceful degradation if unavailable.
- Directories auto-created on startup & config load (data/*).
- Quarantine directory management & hashed filenames.

Generation Pipeline:
- Prompt construction (src/genai/prompts.py) based on alert & actions schema.
- LLM call with temperature 0.1 (Groq/OpenAI/Anthropic) and fallback on error/validation failure.
- YAML cleanup (strip markdown fences) and normalization prior to validation.
- Metadata-based fallback lookup when searching existing playbooks.

API & Integration:
- REST endpoints for playbook generation, retrieval, execution and combined generate-and-run.
- Health endpoint for deployment readiness checks.
- TestClient-based API tests.
- Optional RabbitMQ consumer & file ingestion (decoupled / no blocking during tests).

Operational Safety:
- Admin-only actions skipped automatically to avoid failing entire playbook.
- block_ip & isolate_host clearly gated.
- Deterministic fallback avoids missing coverage when LLM keys absent.

## API Endpoints Reference

| Method | Path | Purpose | Request Body | Success Response (primary fields) |
|--------|------|---------|--------------|------------------------------------|
| GET | /health | Liveness check | N/A | { status: "ok" } |
| POST | /api/playbooks/generate | Generate or reuse playbook | Alert JSON | { status: exists|generated, path } |
| POST | /api/playbooks/generate-and-run | Generate (or reuse) AND immediately execute | Alert JSON | { status, path, playbook_id, result: ExecutionResult } |
| GET | /api/playbooks/{playbook_id} | Retrieve playbook YAML parsed to JSON | N/A | Playbook JSON (schema) |
| POST | /api/executions/run | Execute existing playbook | { playbook_id, alert } | ExecutionResult JSON |
| GET | /api/executions/{execution_id} | Fetch persisted or in-memory execution | N/A | ExecutionResult JSON |

Alert JSON Shape (minimal):
```json
{
  "event_type": "file|process|network",
  "severity": "low|medium|high|critical",
  "agent_id": "string",
  "event_id": "string",
  "details": { "path"|"pid"|"ip": "...", "remote_port": 443 }
}
```

ExecutionResult JSON Shape:
```json
{
  "id": "uuid",
  "playbook_id": "pb-file-medium",
  "success": true,
  "rolled_back": false,
  "steps": [
    {"step": "Quarantine File", "action": "quarantine_file", "status": "ok", "output": {"quarantined_to": "..."}},
    {"step": "Kill Process", "action": "kill_process", "status": "ok", "output": {"status": "killed", "pid": 1234}}
  ]
}
```

## YAML Generation & Normalization Flow

1. Receive alert JSON.
2. Build prompt (system/user messages) including actions schema param requirements.
3. Call provider (if API key present) else create deterministic fallback YAML.
4. Strip markdown fences if any (```yaml ... ``` removed).
5. Normalize structure (version to string; convert shorthand steps / rollback entries to canonical {name, action, params}).
6. Parse with Pydantic; on error fallback to deterministic YAML.
7. Force ID pattern pb-<event_type>-<severity> for consistent retrieval.
8. Persist to data/playbooks/generated/<id>.yaml.
9. Emit audit event playbook_generated.

## Test Suite Coverage

Unit / Parsing:
- `tests/test_parser.py` – Valid YAML parses; invalid action raises PlaybookValidationError.

Executor Action:
- `tests/test_executor.py` – Quarantine flow; asserts success & step status.

GenAI Generation:
- `tests/test_genai.py` – End-to-end generate_playbook -> file persisted -> find_existing_playbook retrieves it after ID normalization & metadata scan.

End-to-End (LLM + Actions): `tests/test_e2e_end_to_end.py`
- File scenario: quarantine temp file; audit increment.
- Process scenario: launch notepad, generate playbook, skip isolate_host if not admin, kill process PID.
- Network scenario: block_ip test IP; skipped unless Admin (firewall rule changes) and Groq key present.

API Generate & Run: `tests/test_api_generate_and_run.py`
- File alert: generate + execute; verifies quarantine.
- Process alert (Windows): kill_process success & PID termination.
- Network alert: block_ip; admin-only skip logic via pytest marker.

Environmental Controls in Tests:
- Disable cooldown/persistence for speed: REDIS_COOLDOWN_ENABLED=false, EXECUTIONS_PERSIST=false.
- Force stub deterministic generator (API tests) with GENAI_PROVIDER=stub.
- Monkeypatch RabbitMQ/file ingestion to no-ops for isolation.

## Future Enhancements (Suggested)

- Linux/macOS implementations for actions (quarantine, process termination, firewall block).
- Rich precondition language (logical AND/OR, numeric comparisons, regex).
- Playbook versioning & diff viewer.
- Signed playbooks / integrity verification before execution.
- Rate limiting per agent beyond Redis cooldown.
- High-level rollback orchestration (partial commit semantics).
- Async parallel step execution (dependency graph) where safe.
- Structured error codes for actions.

## Quick Reference Commands

```powershell
# Run all tests quietly
pytest -q

# Run only API generate-and-run tests
pytest tests/test_api_generate_and_run.py -q

# Run single network test with reason output (requires Admin & key)
pytest -rs tests/test_e2e_end_to_end.py::test_e2e_network_block_ip
```

