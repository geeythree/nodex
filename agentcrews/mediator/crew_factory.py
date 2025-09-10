from typing import List
from .vertical_agents import (
    VerticalAgent, 
    InterpreterAgent, 
    HRPlannerAgent, 
    SalesPlannerAgent, 
    FinancePlannerAgent,
    ComplianceAgent, 
    VisualizerAgent,
    ConversationalRequirementsAgent
)

def create_vertical_crew(domain: str) -> List[VerticalAgent]:
    """Factory function to create a crew of agents based on the business domain."""
    
    # Common agents for all crews
    interpreter = InterpreterAgent()
    requirements_agent = ConversationalRequirementsAgent()
    compliance = ComplianceAgent()
    visualizer = VisualizerAgent()
    
    # Domain-specific planner agent
    if domain == "hr":
        planner = HRPlannerAgent()
        crew = [interpreter, requirements_agent, planner, compliance, visualizer]
    elif domain == "sales":
        planner = SalesPlannerAgent()
        crew = [interpreter, requirements_agent, planner, compliance, visualizer]
    elif domain == "finance":
        planner = FinancePlannerAgent()
        crew = [interpreter, requirements_agent, planner, compliance, visualizer]
    else:  # General or other domains
        # For now, we can use a generic planner or a default crew
        # In a real scenario, you might have a GeneralPlannerAgent
        crew = [interpreter, requirements_agent, compliance, visualizer] # No specific planner
        
    return crew
