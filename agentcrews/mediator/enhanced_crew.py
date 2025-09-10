import os
import yaml
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from crewai import Agent, Task, Crew, Process 
from crewai.project import CrewBase, agent, task, crew
from loguru import logger

from agentcrews.mediator.models import (
    MediatorSession, VoiceInteraction, VoiceInteractionType, 
    UserIntent, AgentResponse, DomainType
)
from agentcrews.mediator.voice_handler import VoiceHandler
from agentcrews.mediator.flow_manager import FlowManager
from agentcrews.mediator.domain_inference import DomainInferenceEngine

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "config")

def load_yaml(filename):
    with open(os.path.join(CONFIG_DIR, filename), "r") as f:
        return yaml.safe_load(f)

@CrewBase
class EnhancedMediatorCrew:
    """Enhanced Mediator Crew with voice, flow management, and compliance integration"""
    
    agents_config = load_yaml("agents.yaml")
    tasks_config = load_yaml("tasks.yaml")
    
    def __init__(self):
        self.voice_handler = VoiceHandler()
        self.flow_manager = FlowManager()
        self.domain_engine = DomainInferenceEngine()
        self.active_sessions: Dict[str, MediatorSession] = {}
        
    @agent
    def interpreter(self) -> Agent:
        """Enhanced interpreter agent with domain awareness"""
        return Agent(
            role="Workflow Interpreter",
            goal="Parse user requirements into actionable workflow steps",
            backstory="Expert at understanding business processes and converting them to executable steps",
            verbose=True,
            llm=os.getenv("CREWAI_MODEL", "gpt-4o")
        )

    @agent
    def planner(self) -> Agent:
        """Enhanced planner agent with compliance awareness"""
        return Agent(
            role="Workflow Planner", 
            goal="Structure workflow steps into logical sequences",
            backstory="System architect specializing in workflow optimization and sequencing",
            verbose=True,
            llm=os.getenv("CREWAI_MODEL", "gpt-4o")
        )

    @agent
    def compliance_agent(self) -> Agent:
        """New compliance agent for domain-specific requirements"""
        return Agent(
            role="Compliance Specialist",
            goal="Inject compliance and security requirements",
            backstory="Compliance expert for multiple domains ensuring regulatory adherence",
            verbose=True,
            llm=os.getenv("CREWAI_MODEL", "gpt-4o")
        )

    @agent
    def visualizer(self) -> Agent:
        """Enhanced visualizer agent with React Flow integration"""
        return Agent(
            role="Workflow Visualizer",
            goal="Generate executable workflow JSON",
            backstory="Expert at creating React Flow compatible workflow definitions",
            verbose=True,
            llm=os.getenv("CREWAI_MODEL", "gpt-4o")
        )

    @task
    def interpret_task(self) -> Task:
        """Enhanced interpretation task with domain inference"""
        config = self.tasks_config["interpret_task"].copy()
        config["description"] += """
        
        Additionally:
        - Identify the likely domain (healthcare, finance, government, education, generic, enterprise)
        - Extract key entities and parameters
        - Note any compliance-sensitive information mentioned
        - Provide confidence score for domain classification
        """
        config["expected_output"] += """
        
        Domain: [identified domain]
        Confidence: [0.0-1.0]
        Key Entities: [list of important entities]
        Compliance Flags: [any compliance-sensitive content]
        """
        return Task(config=config, agent=self.interpreter)

    @task
    def compliance_task(self) -> Task:
        """New task for compliance validation and injection"""
        return Task(
            description="""Based on the interpreted user intent and identified domain, determine required 
            compliance measures and create specifications for mandatory compliance nodes that must be 
            added to the workflow. These nodes should be marked as locked and non-deletable.""",
            expected_output="""List of required compliance nodes with:
            - Node type and label
            - Compliance standard (HIPAA, PCI-DSS, etc.)
            - Description of what the node does
            - Position in workflow (before/after which steps)
            - Lock status (always true for compliance nodes)""",
            agent=self.compliance_agent,
            context=[self.interpret_task]
        )

    @task
    def plan_task(self) -> Task:
        """Enhanced planning task with compliance integration"""
        config = self.tasks_config["plan_task"].copy()
        config["description"] += """
        
        Integrate compliance requirements from the compliance task and ensure:
        - Compliance nodes are positioned correctly in the workflow
        - Dependencies between regular and compliance nodes are respected
        - The workflow maintains logical flow while meeting all requirements
        """
        config["context"] = [self.interpret_task, self.compliance_task]
        return Task(config=config, agent=self.planner)

    @task
    def visualize_task(self) -> Task:
        """Enhanced visualization task with React Flow and compliance support"""
        config = self.tasks_config["visualize_task"].copy()
        config["description"] += """
        
        Create React Flow JSON that includes:
        - Regular workflow nodes (draggable, deletable)
        - Compliance nodes (draggable but not deletable, visually distinct)
        - Proper edge connections maintaining workflow logic
        - Appropriate positioning for visual clarity
        - Node metadata including compliance flags and lock status
        """
        config["expected_output"] = """JSON structure:
        {
          "nodes": [
            {
              "id": "unique_id",
              "type": "input|process|output|compliance|security|audit",
              "data": {
                "label": "Node Label",
                "description": "Node description",
                "locked": true/false,
                "compliance_type": "HIPAA_PHI_REDACTION" (if applicable)
              },
              "position": {"x": 100, "y": 100},
              "draggable": true/false,
              "deletable": true/false
            }
          ],
          "edges": [
            {
              "id": "edge_id",
              "source": "source_node_id",
              "target": "target_node_id",
              "type": "default"
            }
          ]
        }"""
        return Task(config=config, agent=self.visualizer, context=[self.plan_task])

    @crew
    def crew(self) -> Crew:
        """Enhanced crew with compliance agent"""
        return Crew(
            agents=[self.interpreter, self.compliance_agent, self.planner, self.visualizer],
            tasks=[self.interpret_task, self.compliance_task, self.plan_task, self.visualize_task],
            process=Process.sequential,
            verbose=True,
        )

    async def process_voice_input(
        self, 
        audio_file_path: str, 
        user_id: str,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process voice input and create/update workflow"""
        try:
            # Process voice to text
            voice_interaction = await self.voice_handler.process_voice_input(
                audio_file_path, user_id
            )
            
            if not voice_interaction.content or "Error" in voice_interaction.content:
                return {
                    "success": False,
                    "error": "Failed to process voice input",
                    "voice_interaction": voice_interaction.dict()
                }
            
            # Get or create session
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                session.voice_history.append(voice_interaction)
            else:
                # Create new session
                session = self.flow_manager.create_session(
                    user_id=user_id,
                    user_input=voice_interaction.content,
                    title=f"Workflow from voice input"
                )
                session.workflow_state.voice_history.append(voice_interaction)
                self.active_sessions[session.session_id] = session
            
            # Process with crew
            result = await self.process_user_input(
                user_input=voice_interaction.content,
                session_id=session.session_id,
                is_voice=True
            )
            
            # Generate voice response
            if result["success"] and "agent_response" in result:
                voice_response = await self.voice_handler.generate_agent_response(
                    text=result["agent_response"],
                    user_id=user_id
                )
                session.workflow_state.voice_history.append(voice_response)
                result["voice_response"] = voice_response.dict()
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing voice input: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def process_user_input(
        self, 
        user_input: str, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        is_voice: bool = False
    ) -> Dict[str, Any]:
        """Process user input (text or voice) and update workflow"""
        try:
            # Get or create session
            if session_id and session_id in self.active_sessions:
                session = self.active_sessions[session_id]
            elif user_id:
                session = self.flow_manager.create_session(
                    user_id=user_id,
                    user_input=user_input
                )
                self.active_sessions[session.session_id] = session
            else:
                return {
                    "success": False,
                    "error": "Either session_id or user_id is required"
                }
            
            # Update session context
            self.flow_manager.update_session_context(session.session_id, {
                "last_input": user_input,
                "is_voice": is_voice,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Run the crew
            crew_result = self.crew().kickoff(inputs={"user_input": user_input})
            
            # Parse crew result and update flow
            if hasattr(crew_result, 'raw') and crew_result.raw:
                try:
                    # Extract the JSON from the visualizer output
                    import json
                    import re
                    
                    # Look for JSON in the crew output
                    json_match = re.search(r'\{.*\}', crew_result.raw, re.DOTALL)
                    if json_match:
                        flow_json = json.loads(json_match.group())
                        
                        # Update the session's flow with the new structure
                        await self.update_flow_from_crew_output(
                            session.session_id, 
                            flow_json
                        )
                        
                        return {
                            "success": True,
                            "session_id": session.session_id,
                            "flow": session.workflow_state.flow_graph.dict(),
                            "domain": session.workflow_state.domain.value,
                            "agent_response": "I've created your workflow with the necessary compliance components. You can see the flow diagram has been updated with both your requested steps and required compliance measures.",
                            "crew_output": crew_result.raw
                        }
                except Exception as e:
                    logger.error(f"Error parsing crew output: {str(e)}")
            
            return {
                "success": True,
                "session_id": session.session_id,
                "flow": session.workflow_state.flow_graph.dict(),
                "domain": session.workflow_state.domain.value,
                "agent_response": "I've processed your request and updated the workflow.",
                "crew_output": str(crew_result)
            }
            
        except Exception as e:
            logger.error(f"Error processing user input: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def update_flow_from_crew_output(
        self, 
        session_id: str, 
        flow_json: Dict[str, Any]
    ):
        """Update flow based on crew output"""
        try:
            session = self.active_sessions.get(session_id)
            if not session:
                return
            
            # Process nodes from crew output
            if "nodes" in flow_json:
                for node_data in flow_json["nodes"]:
                    # Add or update node
                    await self.flow_manager.process_flow_delta(session_id, {
                        "type": "node_added",
                        "data": node_data
                    })
            
            # Process edges from crew output
            if "edges" in flow_json:
                for edge_data in flow_json["edges"]:
                    await self.flow_manager.process_flow_delta(session_id, {
                        "type": "edge_added",
                        "source": edge_data["source"],
                        "target": edge_data["target"]
                    })
                    
        except Exception as e:
            logger.error(f"Error updating flow from crew output: {str(e)}")

    def get_session(self, session_id: str) -> Optional[MediatorSession]:
        """Get active session"""
        return self.active_sessions.get(session_id)

    async def handle_flow_update(
        self, 
        session_id: str, 
        flow_delta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle manual flow updates from UI"""
        return await self.flow_manager.process_flow_delta(session_id, flow_delta)

    def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        self.flow_manager.cleanup_session(session_id)
