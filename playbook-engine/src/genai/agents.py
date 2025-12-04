"""
Phidata Agents for Multi-Agent Playbook Generation

Three-layer architecture:
1. Requirements Extraction Agent - Analyzes and structures input
2. Playbook Drafting Agent - Creates initial complete draft
3. Review & Refinement Agent - Validates and polishes final output
"""

from phi.agent import Agent
from phi.model.groq import Groq
from typing import Optional


def create_requirements_agent(groq_model: Optional[str] = None) -> Agent:
    """
    Layer 1: Playbook Requirements Extraction Agent
    
    Analyzes alert context and extracts structured requirements
    for playbook generation.
    """
    model = Groq(id=groq_model) if groq_model else Groq(id="llama-3.1-8b-instant")
    
    return Agent(
        name="Security Playbook Requirements Analyst",
        model=model,
        description=(
            "Extract, analyze, and organize all relevant information from security alerts "
            "to create a structured specification for automated response playbooks"
        ),
        instructions=(
            "You are an expert security analyst with deep knowledge of incident response procedures. "
            "Your specialty is analyzing threat alerts and understanding what automated actions are needed. "
            "You excel at identifying the key elements (event type, severity, threat indicators) and "
            "mapping them to appropriate response actions from the available security toolkit. "
            "Provide a structured analysis with threat assessment, recommended actions, required parameters, "
            "preconditions, and rollback strategy."
        ),
        markdown=True,
    )


def create_drafting_agent(groq_model: Optional[str] = None) -> Agent:
    """
    Layer 2: Playbook Drafting Agent
    
    Creates complete, logically structured playbook drafts based on
    extracted requirements.
    """
    model = Groq(id=groq_model) if groq_model else Groq(id="llama-3.1-8b-instant")
    
    return Agent(
        name="Security Playbook Author",
        model=model,
        description=(
            "Generate complete, executable security playbooks in YAML format "
            "that respond appropriately to threats based on analyzed requirements"
        ),
        instructions=(
            "You are a seasoned security engineer who writes automated incident response playbooks. "
            "You have extensive experience creating YAML-based automation scripts for security orchestration platforms. "
            "You understand the importance of clear step definitions, proper parameter specification, "
            "and ensuring playbooks are both effective and safe to execute. You always structure playbooks "
            "with proper metadata, preconditions, action steps, and rollback procedures. "
            "Output ONLY valid YAML with no markdown formatting, code fences, or explanations."
        ),
        markdown=True,
    )


def create_review_agent(groq_model: Optional[str] = None) -> Agent:
    """
    Layer 3: Playbook Review & Refinement Agent
    
    Validates, refines, and finalizes playbooks to ensure quality,
    correctness, and completeness.
    """
    model = Groq(id=groq_model) if groq_model else Groq(id="llama-3.1-8b-instant")
    
    return Agent(
        name="Senior Security Playbook Reviewer",
        model=model,
        description=(
            "Review and refine security playbooks to ensure they are accurate, complete, "
            "properly formatted, and safe to execute in production environments"
        ),
        instructions=(
            "You are a senior security architect with years of experience reviewing and approving "
            "automated response procedures. Your keen eye catches inconsistencies, missing steps, "
            "and potential safety issues. You ensure playbooks follow best practices, have proper "
            "error handling, and align with security operations standards. You validate YAML syntax, "
            "check parameter completeness, and verify that each playbook will execute as intended. "
            "You polish the final output to be production-ready. "
            "Output ONLY the final refined YAML with no markdown formatting, code fences, or explanations."
        ),
        markdown=True,
    )
