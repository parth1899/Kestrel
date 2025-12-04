"""
Phidata Orchestrator for Multi-Agent Playbook Generation

Coordinates the three-agent pipeline:
1. Requirements Extraction → 2. Playbook Drafting → 3. Review & Refinement
"""

from typing import Dict, Any, Optional
from .agents import (
    create_requirements_agent,
    create_drafting_agent,
    create_review_agent,
)
from .tasks import (
    create_requirements_task_prompt,
    create_drafting_task_prompt,
    create_review_task_prompt,
)


class PlaybookGenerationCrew:
    """
    Three-layer multi-agent system for generating security playbooks.
    
    Architecture:
    - Layer 1: Requirements Extraction Agent analyzes alerts
    - Layer 2: Drafting Agent creates complete playbook
    - Layer 3: Review Agent validates and refines output
    """
    
    def __init__(self, groq_model: Optional[str] = None):
        """
        Initialize the crew with three specialized agents.
        
        Args:
            groq_model: Optional Groq model name (e.g., 'llama-3.1-8b-instant')
        """
        self.groq_model = groq_model or "llama-3.1-8b-instant"
        self.requirements_agent = create_requirements_agent(self.groq_model)
        self.drafting_agent = create_drafting_agent(self.groq_model)
        self.review_agent = create_review_agent(self.groq_model)
    
    def generate_playbook(self, alert: Dict[str, Any], actions_catalog: str) -> str:
        """
        Execute the three-agent pipeline to generate a refined playbook.
        
        Pipeline flow:
        1. Requirements agent analyzes alert and creates structured requirements
        2. Drafting agent creates complete YAML playbook
        3. Review agent validates and refines the playbook
        
        Args:
            alert: Security alert dictionary with event_type, severity, details
            actions_catalog: String describing available actions and their parameters
        
        Returns:
            Final YAML playbook string (validated and refined)
        """
        # Step 1: Requirements extraction
        requirements_prompt = create_requirements_task_prompt(alert, actions_catalog)
        requirements_result = self.requirements_agent.run(requirements_prompt)
        
        # Step 2: Playbook drafting
        drafting_context = f"""
Based on these requirements:
{requirements_result}

Now create the playbook:
"""
        drafting_prompt = create_drafting_task_prompt(alert)
        drafting_result = self.drafting_agent.run(drafting_context + drafting_prompt)
        
        # Step 3: Review and refinement
        review_context = f"""
Here is the draft playbook to review:
{drafting_result}

Now provide the final refined version:
"""
        review_prompt = create_review_task_prompt(alert)
        final_playbook = self.review_agent.run(review_context + review_prompt)
        
        return final_playbook


def create_crew(groq_model: Optional[str] = None) -> PlaybookGenerationCrew:
    """
    Factory function to create a new playbook generation crew.
    
    Args:
        groq_model: Optional Groq model name
    
    Returns:
        Initialized PlaybookGenerationCrew instance
    """
    return PlaybookGenerationCrew(groq_model=groq_model)
