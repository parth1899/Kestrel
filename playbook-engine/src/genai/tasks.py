"""
CrewAI Tasks for Multi-Agent Playbook Generation

Defines the three sequential tasks that agents perform:
1. Extract and structure requirements from alert
2. Draft complete playbook based on requirements
3. Review and refine playbook to final production quality
"""

from crewai import Task
from crewai import Agent
from typing import Dict, Any


def create_requirements_task(agent: Agent, alert: Dict[str, Any], actions_catalog: str) -> Task:
    """
    Task 1: Extract Requirements
    
    Analyzes the alert and available actions to create a structured
    specification for playbook generation.
    """
    alert_summary = (
        f"Event Type: {alert.get('event_type', 'unknown')}\n"
        f"Severity: {alert.get('severity', 'unknown')}\n"
        f"Agent ID: {alert.get('agent_id', 'unknown')}\n"
        f"Details: {alert.get('details', {})}"
    )
    
    description = f"""
Analyze the following security alert and extract all requirements needed to create an automated response playbook:

ALERT INFORMATION:
{alert_summary}

AVAILABLE ACTIONS:
{actions_catalog}

YOUR TASK:
1. Identify the threat type and severity level
2. Determine which action(s) from the available catalog are most appropriate
3. Extract all required parameters for the chosen action(s) from the alert details
4. Define any preconditions that should be checked before execution
5. Suggest appropriate rollback steps if needed
6. Structure this into a clear requirements specification

OUTPUT FORMAT:
Provide a structured analysis with:
- Threat Assessment (event type, severity, key indicators)
- Recommended Actions (which actions to use and why)
- Required Parameters (what values are needed for each action)
- Preconditions (what should be checked before running)
- Rollback Strategy (how to undo actions if needed)
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            "A structured requirements specification containing threat assessment, "
            "recommended actions, required parameters, preconditions, and rollback strategy"
        ),
    )


def create_drafting_task(agent: Agent, alert: Dict[str, Any]) -> Task:
    """
    Task 2: Draft Playbook
    
    Creates a complete YAML playbook based on the requirements
    extracted in Task 1.
    """
    event_type = alert.get("event_type", "unknown")
    severity = alert.get("severity", "medium")
    
    description = f"""
Based on the requirements specification from the previous analysis, generate a complete security playbook in YAML format.

PLAYBOOK REQUIREMENTS:
- Event Type: {event_type}
- Severity: {severity}
- Target Format: YAML

YOUR TASK:
Create a fully executable playbook with the following structure:

```yaml
id: pb-{event_type}-{severity}
version: "1.0"
metadata:
  event_type: {event_type}
  severity: {severity}
  description: <brief description of what this playbook does>
preconditions:
  - field: <field to check>
    operator: <equals or contains>
    value: <expected value>
steps:
  - name: <descriptive step name>
    action: <action name from available actions>
    params:
      <param_name>: <param_value>
rollback:
  - name: <rollback step name>
    action: <rollback action>
    params:
      <param_name>: <param_value>
```

IMPORTANT GUIDELINES:
1. Use the exact action names from the available actions catalog
2. Include all required parameters for each action
3. Set meaningful step names that describe what each action does
4. Add preconditions to validate the alert before execution
5. Include rollback steps to undo actions if something goes wrong
6. Ensure the YAML is properly formatted and syntactically correct
7. The playbook ID must follow the pattern: pb-<event_type>-<severity>

OUTPUT:
Provide ONLY the complete YAML playbook, with no additional text or markdown formatting.
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            f"A complete YAML playbook with id 'pb-{event_type}-{severity}' containing "
            "metadata, preconditions, action steps with parameters, and rollback procedures"
        ),
    )


def create_review_task(agent: Agent, alert: Dict[str, Any]) -> Task:
    """
    Task 3: Review & Refine
    
    Validates and polishes the drafted playbook to ensure it's
    production-ready and meets all quality standards.
    """
    event_type = alert.get("event_type", "unknown")
    severity = alert.get("severity", "medium")
    
    description = f"""
Review and refine the security playbook draft to ensure it is production-ready.

YOUR TASK:
Perform a comprehensive review of the playbook and check for:

1. STRUCTURAL COMPLETENESS
   - Does it have all required sections (id, version, metadata, steps)?
   - Is the YAML syntax valid?
   - Are all required fields present?

2. CORRECTNESS
   - Does the playbook ID follow the pattern: pb-{event_type}-{severity}?
   - Are action names valid and from the available catalog?
   - Are all required parameters included for each action?
   - Do parameter values match the alert details?

3. LOGICAL CONSISTENCY
   - Do preconditions make sense for this alert type?
   - Are the steps in a logical order?
   - Are rollback steps appropriate for the actions taken?

4. CLARITY & POLISH
   - Are step names clear and descriptive?
   - Is the description accurate?
   - Is the overall structure clean and readable?

5. SAFETY
   - Are there any potentially dangerous combinations of actions?
   - Are rollback procedures adequate?
   - Will this playbook execute safely?

OUTPUT:
Provide the FINAL, REFINED YAML playbook with all improvements applied.
Output ONLY the YAML content with no markdown code fences, explanations, or additional text.
The output should be ready to be parsed directly as YAML.
"""
    
    return Task(
        description=description,
        agent=agent,
        expected_output=(
            f"A polished, production-ready YAML playbook for {event_type}/{severity} alerts "
            "with validated syntax, complete parameters, and proper structure"
        ),
    )
