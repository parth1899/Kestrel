"""
CrewAI Crew Orchestrator for Multi-Agent Playbook Generation

Coordinates the three-agent pipeline:
1. Requirements Extraction → 2. Playbook Drafting → 3. Review & Refinement
"""

from crewai import Crew, Process
from typing import Dict, Any
from .agents import (
    create_requirements_agent,
    create_drafting_agent,
    create_review_agent,
)
from .tasks import (
    create_requirements_task,
    create_drafting_task,
    create_review_task,
)


class PlaybookGenerationCrew:
    """
    Three-layer multi-agent system for generating security playbooks.
    
    Architecture:
    - Layer 1: Requirements Extraction Agent analyzes alerts
    - Layer 2: Drafting Agent creates complete playbook
    - Layer 3: Review Agent validates and refines output
    """
    
    def __init__(self, llm: str = None):
        """
        Initialize the crew with three specialized agents.
        
        Args:
            llm: Optional LLM configuration string (e.g., 'groq/llama-3.1-8b-instant')
        """
        self.llm = llm
        self.requirements_agent = create_requirements_agent(llm)
        self.drafting_agent = create_drafting_agent(llm)
        self.review_agent = create_review_agent(llm)
    
    def generate_playbook(self, alert: Dict[str, Any], actions_catalog: str) -> str:
        """
        Execute the three-agent pipeline to generate a refined playbook.
        
        Args:
            alert: Security alert dictionary with event_type, severity, details
            actions_catalog: String describing available actions and their parameters
        
        Returns:
            Final YAML playbook string (validated and refined)
        """
        # Create the three sequential tasks
        task1 = create_requirements_task(
            agent=self.requirements_agent,
            alert=alert,
            actions_catalog=actions_catalog
        )
        
        task2 = create_drafting_task(
            agent=self.drafting_agent,
            alert=alert
        )
        
        task3 = create_review_task(
            agent=self.review_agent,
            alert=alert
        )
        
        # Create crew with sequential process
        crew = Crew(
            agents=[
                self.requirements_agent,
                self.drafting_agent,
                self.review_agent,
            ],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=True,
        )
        
        # Execute the pipeline
        result = crew.kickoff()
        
        # Extract the final YAML from the result
        if hasattr(result, 'raw'):
            return result.raw
        elif isinstance(result, str):
            return result
        else:
            return str(result)


def create_crew(llm: str = None) -> PlaybookGenerationCrew:
    """
    Factory function to create a new playbook generation crew.
    
    Args:
        llm: Optional LLM configuration string
    
    Returns:
        Initialized PlaybookGenerationCrew instance
    """
    return PlaybookGenerationCrew(llm=llm)
