import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import openai
import os

from .models import DomainType, FlowNode, NodeType, NodeData, Position
from .domain_inference import DomainInferenceEngine

class WorkflowIntent(BaseModel):
    """Represents the parsed intent from user input"""
    description: str
    domain: DomainType
    workflow_steps: List[Dict[str, Any]]
    connections: List[Dict[str, str]]
    complexity: str = Field(..., description="simple, medium, complex")

class WorkflowAnalysisTool(BaseTool):
    """Tool for analyzing user intent and generating workflow structure"""
    name: str = "workflow_analyzer"
    description: str = "Analyzes user input to understand workflow intent and generate node structure"
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **kwargs):
        super().__init__(name="workflow_analyzer", description="Analyzes user input to understand workflow intent and generate node structure", **kwargs)
    
    def _run(self, user_input: str) -> str:
        """Analyze user input and return workflow structure"""
        try:
            # This would typically call an LLM API to analyze the input
            # For now, we'll return a structured format that the agent can work with
            analysis = {
                "user_input": user_input,
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "suggested_approach": "dynamic_workflow_generation"
            }
            return json.dumps(analysis)
        except Exception as e:
            return f"Analysis error: {str(e)}"

class WorkflowGenerationResponse(BaseModel):
    """Response from workflow generation"""
    success: bool
    message: str
    workflow: Dict[str, Any]
    summary: str
    error: Optional[str] = None

class WorkflowGenerationAgent:
    """AI Agent that generates new workflows from collected requirements"""
    
    def __init__(self):
        self.domain_engine = DomainInferenceEngine()
        self.openai_client = None
        self._initialize_client()
        
    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            return
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
    
    async def generate_workflow_from_requirements(self, requirements: Dict[str, Any]) -> WorkflowGenerationResponse:
        """Generate workflow from collected requirements"""
        logger.info(f"Generating workflow from requirements: {requirements}")
        
        if not self.openai_client:
            return self._fallback_generation(requirements)
        
        try:
            workflow_structure = await self._generate_ai_workflow_from_requirements(requirements)
            
            summary = f"I've created a workflow for {requirements.get('process_name', 'your process')} with {len(workflow_structure.get('nodes', []))} steps."
            
            return WorkflowGenerationResponse(
                success=True,
                message="I've successfully created your workflow based on the requirements we discussed.",
                workflow=workflow_structure,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"AI workflow generation failed: {str(e)}")
            return self._fallback_generation(requirements)
    
    async def _generate_ai_workflow_from_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI to generate workflow from structured requirements"""
        
        system_prompt = """You are an expert business workflow architect. You receive structured requirements and create comprehensive workflows.

        Your focus is on creating workflows for:
        - Employee onboarding and HR processes
        - Document approval and review workflows  
        - Financial approval and expense management
        - Compliance reporting and audit trails
        - Internal communication and notification flows
        - Data processing and validation workflows
        - Quality assurance and review processes

        Rules:
        1. Create 3-6 nodes based on complexity
        2. Always include compliance nodes when required
        3. Use clear, business-appropriate labels
        4. Connect nodes in logical sequence
        5. Include approval steps where needed
        6. Consider stakeholder roles in node design

        Return ONLY a JSON object with this exact structure:
        {
          "nodes": [
            {
              "id": "unique_id",
              "type": "input|process|output|approval",
              "data": {
                "label": "Business Action Label",
                "description": "Clear business description",
                "locked": false,
                "compliance_type": "GDPR|HIPAA|SOX|PCI|null"
              },
              "position": {"x": 100, "y": 200}
            }
          ],
          "edges": [
            {
              "id": "edge_id",
              "source": "source_node_id", 
              "target": "target_node_id",
              "type": "default",
              "animated": false,
              "label": ""
            }
          ]
        }"""

        user_prompt = f"""Create a workflow based on these requirements:

        {json.dumps(requirements, indent=2)}

        Generate a complete workflow that addresses all the specified requirements, stakeholders, and compliance needs."""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            ai_response = response.choices[0].message.content.strip()
            logger.info(f"OpenAI workflow generation response: {ai_response}")
            
            workflow_data = json.loads(ai_response)
            
            # Add unique IDs and positions if missing
            for i, node in enumerate(workflow_data.get("nodes", [])):
                if not node.get("id"):
                    node["id"] = f"gen_node_{uuid.uuid4().hex[:8]}"
                if not node.get("position"):
                    node["position"] = {"x": 100 + (i * 250), "y": 200}
            
            # Generate edges if missing
            if not workflow_data.get("edges") and len(workflow_data.get("nodes", [])) > 1:
                workflow_data["edges"] = []
                nodes = workflow_data["nodes"]
                for i in range(len(nodes) - 1):
                    edge = {
                        "id": f"edge_{nodes[i]['id']}_{nodes[i+1]['id']}",
                        "source": nodes[i]["id"],
                        "target": nodes[i+1]["id"],
                        "type": "default",
                        "animated": False,
                        "label": ""
                    }
                    workflow_data["edges"].append(edge)
            
            return workflow_data
                
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise e
    
    def _fallback_generation(self, requirements: Dict[str, Any]) -> WorkflowGenerationResponse:
        """Create a simple workflow as fallback"""
        process_name = requirements.get('process_name', 'Process')
        
        nodes = [
            {
                "id": f"input_{uuid.uuid4().hex[:8]}",
                "type": "input",
                "data": {
                    "label": f"{process_name} Request",
                    "description": f"Initial request for {process_name.lower()}",
                    "locked": False,
                    "compliance_type": None
                },
                "position": {"x": 100, "y": 200}
            },
            {
                "id": f"process_{uuid.uuid4().hex[:8]}",
                "type": "process",
                "data": {
                    "label": f"Process {process_name}",
                    "description": f"Main processing step for {process_name.lower()}",
                    "locked": False,
                    "compliance_type": None
                },
                "position": {"x": 350, "y": 200}
            },
            {
                "id": f"output_{uuid.uuid4().hex[:8]}",
                "type": "output",
                "data": {
                    "label": f"{process_name} Complete",
                    "description": f"Completion of {process_name.lower()}",
                    "locked": False,
                    "compliance_type": None
                },
                "position": {"x": 600, "y": 200}
            }
        ]
        
        edges = [
            {
                "id": f"edge_{nodes[0]['id']}_{nodes[1]['id']}",
                "source": nodes[0]["id"],
                "target": nodes[1]["id"],
                "type": "default",
                "animated": False,
                "label": ""
            },
            {
                "id": f"edge_{nodes[1]['id']}_{nodes[2]['id']}",
                "source": nodes[1]["id"],
                "target": nodes[2]["id"],
                "type": "default",
                "animated": False,
                "label": ""
            }
        ]
        
        return WorkflowGenerationResponse(
            success=True,
            message="I've created a basic workflow structure. You can now modify it using editing commands.",
            workflow={"nodes": nodes, "edges": edges},
            summary=f"Created a basic {process_name} workflow with 3 steps."
        )
