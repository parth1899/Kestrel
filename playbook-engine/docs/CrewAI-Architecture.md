# CrewAI Multi-Agent Playbook Generation Architecture

## Overview

The playbook generation system has been upgraded from a single LLM call to a sophisticated **three-layer multi-agent architecture** using CrewAI. This provides improved quality, reasoning, and validation of generated playbooks while maintaining complete backward compatibility.

## Architecture

### Three-Agent Pipeline

The system employs a sequential multi-agent workflow where each agent specializes in a specific aspect of playbook generation:

```
Alert Input → Agent 1 (Requirements) → Agent 2 (Drafting) → Agent 3 (Review) → Final Playbook
```

### 1. Requirements Extraction Agent (Layer 1)

**Role:** Security Playbook Requirements Analyst

**Responsibilities:**
- Parse and analyze security alert data
- Extract event type, severity, and threat indicators
- Identify appropriate response actions from available catalog
- Determine required parameters from alert details
- Define preconditions for execution
- Suggest rollback strategies

**Output:** Structured requirements specification for playbook creation

**Implementation:** `src/genai/agents.py::create_requirements_agent()`

### 2. Playbook Drafting Agent (Layer 2)

**Role:** Security Playbook Author

**Responsibilities:**
- Generate complete YAML playbook based on requirements
- Structure playbook with proper metadata, steps, and rollback
- Ensure all required parameters are included
- Follow YAML formatting conventions
- Apply security best practices
- Create clear, descriptive step names

**Output:** Complete draft YAML playbook

**Implementation:** `src/genai/agents.py::create_drafting_agent()`

### 3. Review & Refinement Agent (Layer 3)

**Role:** Senior Security Playbook Reviewer

**Responsibilities:**
- Validate YAML syntax and structure
- Check for factual consistency and completeness
- Verify parameter accuracy against alert data
- Ensure proper ID format (pb-{event_type}-{severity})
- Remove redundancy and improve clarity
- Validate safety and executability
- Polish final output for production

**Output:** Refined, production-ready YAML playbook

**Implementation:** `src/genai/agents.py::create_review_agent()`

## Technical Implementation

### Core Components

#### 1. Agents Module (`src/genai/agents.py`)
Defines the three specialized agents with:
- Specific roles and goals
- Detailed backstories for context
- No delegation (focused execution)
- Configurable LLM support

#### 2. Tasks Module (`src/genai/tasks.py`)
Creates sequential tasks for each agent:
- `create_requirements_task()` - Extract and structure requirements
- `create_drafting_task()` - Generate complete YAML draft
- `create_review_task()` - Validate and refine output

#### 3. Crew Orchestrator (`src/genai/crew.py`)
Coordinates the multi-agent pipeline:
- `PlaybookGenerationCrew` class manages the three agents
- Sequential process ensures proper information flow
- Returns final polished YAML playbook

#### 4. Generator Integration (`src/genai/generator.py`)
Modified to use CrewAI pipeline:
- Detects CrewAI availability
- Falls back to single LLM call if unavailable
- Maintains all existing normalization and validation
- Preserves deterministic fallback for offline mode

### Execution Flow

```python
# In generator.py::generate_playbook()

1. Load configuration and actions catalog
2. Build actions description for agents
3. Check provider and API keys

IF CrewAI available AND provider != "stub":
    4a. Create three-agent crew
    4b. Execute sequential pipeline
    4c. Receive refined YAML from Review Agent
ELSE:
    4d. Fall back to single LLM call or deterministic generation

5. Normalize YAML structure
6. Validate against schema
7. Enforce playbook ID pattern
8. Persist to generated directory
9. Audit and return path
```

### Fallback Hierarchy

The system maintains multiple fallback layers for reliability:

1. **Primary:** CrewAI multi-agent pipeline (if available and configured)
2. **Secondary:** Single LLM call (OpenAI/Anthropic/Groq)
3. **Tertiary:** Deterministic YAML generation (offline/stub mode)

## Backward Compatibility

### ✅ Preserved API Contracts

**No changes to:**
- Request schemas (`AlertIn` model)
- Response schemas (Path return type, ExecutionResult)
- Endpoint signatures
- Input/output data structures

**Endpoints remain identical:**
- `POST /api/playbooks/generate`
- `POST /api/playbooks/generate-and-run`
- `GET /api/playbooks/{playbook_id}`

### Configuration

CrewAI integration is transparent and requires no configuration changes:

```yaml
# config/config.yaml - no changes needed
genai:
  provider: groq  # or openai, anthropic
  model: llama-3.1-8b-instant
  groq_api_key: "your-key-here"
```

The system automatically:
- Detects CrewAI availability
- Uses multi-agent pipeline when possible
- Falls back gracefully if not installed

### Testing Modes

Tests continue to work unchanged:

```bash
# API tests use stub provider (deterministic)
GENAI_PROVIDER=stub pytest tests/test_api_generate_and_run.py

# E2E tests use real LLM (CrewAI if available)
pytest tests/test_e2e_end_to_end.py
```

## Benefits of Multi-Agent Architecture

### 1. **Improved Quality**
- Three specialized agents ensure thorough analysis
- Review layer catches errors and inconsistencies
- Better parameter extraction from complex alerts

### 2. **Enhanced Reasoning**
- Requirements agent provides structured analysis
- Drafting agent focuses solely on YAML generation
- Review agent applies critical validation

### 3. **Better Validation**
- Explicit review step before finalization
- Checks for completeness, correctness, and safety
- Ensures production-ready output

### 4. **Maintainability**
- Clear separation of concerns
- Each agent has focused responsibility
- Easy to enhance individual agents

### 5. **Transparency**
- Each agent logs its reasoning (verbose=True)
- Clear audit trail of generation process
- Easier debugging and refinement

## Dependencies

New dependencies added to `req.txt`:

```plaintext
crewai>=0.51.0
crewai-tools>=0.12.0
```

Install with:

```bash
pip install -r req.txt
```

## Usage Examples

### Standard API Usage (Unchanged)

```python
# POST to /api/playbooks/generate
alert = {
    "event_type": "process",
    "severity": "high",
    "agent_id": "agent-001",
    "details": {"pid": 1234}
}

# Automatically uses CrewAI if available, falls back gracefully
response = client.post("/api/playbooks/generate", json=alert)
```

### Programmatic Usage

```python
from src.genai.generator import generate_playbook

alert = {
    "event_type": "file",
    "severity": "medium",
    "details": {"path": "C:/malware.exe"}
}

# Uses CrewAI multi-agent pipeline automatically
playbook_path = await generate_playbook(alert)
```

## Performance Considerations

### Execution Time
- **Single LLM:** ~2-5 seconds per playbook
- **CrewAI Pipeline:** ~8-15 seconds per playbook (3x LLM calls + coordination)

The increased time is justified by significantly improved output quality.

### Cost
- CrewAI makes 3 LLM API calls per playbook (vs. 1 for single call)
- Consider this when using paid API providers
- Deterministic fallback (stub mode) remains free and fast for testing

## Monitoring & Debugging

### Logging

CrewAI agents log their reasoning:

```python
# In logs/app.log
INFO - Using CrewAI multi-agent pipeline with groq/llama-3.1-8b-instant
INFO - Agent: Security Playbook Requirements Analyst
INFO - Task: Analyzing alert for requirements...
INFO - Agent: Security Playbook Author
INFO - Task: Drafting YAML playbook...
INFO - Agent: Senior Security Playbook Reviewer
INFO - Task: Reviewing and refining playbook...
```

### Fallback Indicators

```python
WARNING - CrewAI not available; will use single LLM call fallback
WARNING - CrewAI pipeline failed: <error>; falling back to single LLM call
```

## Future Enhancements

Potential improvements to the multi-agent system:

1. **Tool Integration:** Add CrewAI tools for file/database access
2. **Memory:** Enable agent memory for learning from past playbooks
3. **Collaboration:** Allow agents to delegate sub-tasks
4. **Custom Agents:** Add domain-specific agents (network, file, process)
5. **Feedback Loop:** Incorporate execution results into future generation

## Troubleshooting

### CrewAI Not Being Used

**Check:**
1. Is `crewai` installed? (`pip list | grep crewai`)
2. Is provider set to "stub"? (CrewAI skipped in stub mode)
3. Is API key present for the provider?
4. Check logs for import errors

### Playbook Quality Issues

**Solutions:**
1. Review agent backstories in `agents.py` for clearer instructions
2. Enhance task descriptions in `tasks.py` with more examples
3. Adjust LLM model (larger models = better reasoning)
4. Add validation rules to Review Agent

### Performance Issues

**Optimizations:**
1. Use faster LLM models (e.g., GPT-3.5 vs GPT-4)
2. Reduce agent verbosity (`verbose=False`)
3. Cache generated playbooks (already implemented via `find_existing_playbook`)
4. Use deterministic mode for testing

## Summary

The CrewAI multi-agent architecture represents a significant upgrade to the playbook generation system:

- ✅ **Zero breaking changes** - Full API backward compatibility
- ✅ **Improved quality** - Three-layer validation and refinement
- ✅ **Graceful degradation** - Multiple fallback mechanisms
- ✅ **Production-ready** - Tested with existing test suite
- ✅ **Transparent integration** - No configuration changes required

The system automatically leverages CrewAI when available while maintaining robust fallback behavior for reliability and offline operation.
