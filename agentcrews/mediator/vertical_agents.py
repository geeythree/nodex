from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
from loguru import logger
import openai
from .workflow_templates import get_template, get_domain_templates, WORKFLOW_TEMPLATES

# Base class for all specialized agents
class VerticalAgent(BaseModel):
    name: str
    description: str

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Each agent must implement its own processing logic."""
        raise NotImplementedError

# --- HR Agents ---
class HRPlannerAgent(VerticalAgent):
    name: str = "HR Planner Agent"
    description: str = "Designs HR-related workflows like onboarding and reviews."

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # In a real implementation, this would generate HR-specific workflow steps
        return {"message": f"HR workflow plan for '{text}' created."}

# --- Sales Agents ---
class SalesPlannerAgent(VerticalAgent):
    name: str = "Sales Planner Agent"
    description: str = "Designs sales workflows like lead qualification and routing."

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"message": f"Sales workflow plan for '{text}' created."}

# --- Finance Agents ---
class FinancePlannerAgent(VerticalAgent):
    name: str = "Finance Planner Agent"
    description: str = "Designs finance workflows like expense approvals and invoicing."

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"message": f"Finance workflow plan for '{text}' created."}

# --- Common Agents (can be used across crews) ---
class InterpreterAgent(VerticalAgent):
    name: str = "Interpreter Agent"
    description: str = "Understands and translates user requests into structured data."

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"interpreted_text": text, "entities": {}}

class ComplianceAgent(VerticalAgent):
    name: str = "Compliance Agent"
    description: str = "Ensures the workflow adheres to relevant compliance standards."

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"compliance_check": "passed", "message": "Workflow is compliant."}

class VisualizerAgent(VerticalAgent):
    name: str = "Visualizer Agent"
    description: str = "Generates the visual representation of the workflow for React Flow."
    openai_client: Any = None
    
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=api_key)

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate or modify workflow visualization based on user request and existing state"""
        
        domain = context.get('domain', 'general')
        existing_workflow = context.get('existing_workflow', {})
        existing_nodes = existing_workflow.get('nodes', [])
        existing_edges = existing_workflow.get('edges', [])
        
        # Analyze user request to determine what changes to make
        if not self.openai_client:
            # Fallback: if no existing workflow, create basic template
            if not existing_nodes:
                template = self._get_basic_template(domain)
                return {
                    "nodes": template["nodes"],
                    "edges": template["edges"],
                    "message": f"Created basic {domain} workflow template."
                }
            else:
                return {
                    "nodes": existing_nodes,
                    "edges": existing_edges,
                    "message": "Workflow visualization maintained."
                }

        # Use AI to determine what modifications to make
        system_prompt = f"""You are a workflow visualization agent. Based on the user's request and existing workflow, determine what nodes and edges to add, modify, or remove.

        Current workflow has {len(existing_nodes)} nodes and {len(existing_edges)} edges.
        
        Analyze the user request and return JSON with:
        - action: "add_nodes", "modify_nodes", "remove_nodes", "add_edges", "remove_edges", or "create_new"
        - nodes_to_add: array of new nodes to add (if action involves adding)
        - edges_to_add: array of new edges to add (if action involves adding)
        - nodes_to_remove: array of node IDs to remove (if action involves removing)
        - edges_to_remove: array of edge IDs to remove (if action involves removing)
        - message: description of changes made
        
        Node format: {{"id": "unique_id", "type": "input|process|output", "data": {{"label": "Node Name", "description": "Description"}}, "position": {{"x": number, "y": number}}}}
        Edge format: {{"id": "edge_id", "source": "source_node_id", "target": "target_node_id"}}
        
        For {domain} domain, ensure compliance nodes are included when creating new workflows.
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User request: '{text}'\nExisting nodes: {[n.get('data', {}).get('label', n.get('id')) for n in existing_nodes]}\nDetermine what changes to make to the workflow."}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Apply the changes to existing workflow
            updated_nodes = existing_nodes.copy()
            updated_edges = existing_edges.copy()
            
            # Handle node additions
            if result.get("nodes_to_add"):
                for node in result["nodes_to_add"]:
                    # Ensure unique IDs
                    existing_ids = {n.get('id') for n in updated_nodes}
                    if node.get('id') not in existing_ids:
                        updated_nodes.append(node)
            
            # Handle edge additions
            if result.get("edges_to_add"):
                for edge in result["edges_to_add"]:
                    # Ensure unique edges
                    existing_edge_pairs = {(e.get('source'), e.get('target')) for e in updated_edges}
                    if (edge.get('source'), edge.get('target')) not in existing_edge_pairs:
                        updated_edges.append(edge)
            
            # Handle node removals
            if result.get("nodes_to_remove"):
                updated_nodes = [n for n in updated_nodes if n.get('id') not in result["nodes_to_remove"]]
            
            # Handle edge removals
            if result.get("edges_to_remove"):
                updated_edges = [e for e in updated_edges if e.get('id') not in result["edges_to_remove"]]
            
            # If creating new workflow and no existing nodes, use template as base
            if result.get("action") == "create_new" and not existing_nodes:
                template = self._get_workflow_template(domain, text)
                if template:
                    updated_nodes = template["nodes"]
                    updated_edges = template["edges"]
            
            return {
                "nodes": updated_nodes,
                "edges": updated_edges,
                "message": result.get("message", "Workflow updated successfully."),
                "action": result.get("action", "modify")
            }
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {e}")
            # Fallback: return existing workflow or basic template
            if existing_nodes:
                return {
                    "nodes": existing_nodes,
                    "edges": existing_edges,
                    "message": "Maintained existing workflow due to processing error."
                }
            else:
                template = self._get_basic_template(domain)
                return {
                    "nodes": template["nodes"],
                    "edges": template["edges"],
                    "message": f"Created basic {domain} workflow."
                }

    def _get_basic_template(self, domain: str) -> Dict[str, Any]:
        """Get a basic workflow template for the domain"""
        base_nodes = [
            {
                "id": "start",
                "type": "input",
                "data": {"label": "Start", "description": "Workflow initiation"},
                "position": {"x": 100, "y": 100}
            },
            {
                "id": "process",
                "type": "process", 
                "data": {"label": f"{domain.title()} Process", "description": f"Main {domain} processing step"},
                "position": {"x": 300, "y": 100}
            },
            {
                "id": "compliance",
                "type": "process",
                "data": {"label": "Compliance Check", "description": "Regulatory compliance validation"},
                "position": {"x": 500, "y": 100}
            },
            {
                "id": "complete",
                "type": "output",
                "data": {"label": "Complete", "description": "Workflow completion"},
                "position": {"x": 700, "y": 100}
            }
        ]
        
        base_edges = [
            {"id": "e1", "source": "start", "target": "process"},
            {"id": "e2", "source": "process", "target": "compliance"},
            {"id": "e3", "source": "compliance", "target": "complete"}
        ]
        
        return {"nodes": base_nodes, "edges": base_edges}

    def _get_workflow_template(self, domain: str, text: str) -> Dict[str, Any]:
        """Get a workflow template based on domain and user request"""
        try:
            from .workflow_templates import WORKFLOW_TEMPLATES
            
            if domain in WORKFLOW_TEMPLATES:
                domain_templates = WORKFLOW_TEMPLATES[domain]
                user_text = text.lower()
                
                # Match templates based on keywords in user request
                if domain == "hr" and ("onboarding" in user_text or "employee" in user_text):
                    template = domain_templates.get("employee_onboarding")
                elif domain == "finance" and ("expense" in user_text or "approval" in user_text):
                    template = domain_templates.get("expense_approval")
                elif domain == "sales" and ("lead" in user_text or "qualification" in user_text):
                    template = domain_templates.get("lead_qualification")
                else:
                    # Use the first available template for the domain
                    template = list(domain_templates.values())[0] if domain_templates else None
                
                if template:
                    # Convert template to nodes and edges format
                    nodes = []
                    for step in template.steps:
                        node = {
                            "id": step.id,
                            "type": "default",
                            "position": step.position,
                            "data": {
                                "label": step.label,
                                "description": getattr(step, 'description', ''),
                                "assigned_user": step.assigned_user,
                                "type": step.type,
                                "compliance": step.compliance_requirements,
                                "inputs": step.inputs,
                                "outputs": step.outputs
                            },
                            "style": step.style
                        }
                        nodes.append(node)
                    
                    return {
                        "nodes": nodes,
                        "edges": template.edges
                    }
            
            # Fallback to basic template
            return self._get_basic_template(domain)
            
        except Exception as e:
            logger.error(f"Error getting workflow template: {e}")
            return self._get_basic_template(domain)

# --- Requirement Gathering Agent ---
class ConversationalRequirementsAgent(VerticalAgent):
    name: str = "Conversational Requirements Agent"
    description: str = "Gathers detailed requirements through conversational interaction."
    openai_client: Any = None
    
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=api_key)

    async def process(self, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze if more requirements are needed and gather them conversationally"""
        
        # Check if this is a direct workflow editing command
        editing_keywords = [
            "remove", "delete", "add", "connect", "disconnect", "move", "change", 
            "modify", "update", "edit", "insert", "replace", "rename", "position",
            "color", "style", "link", "unlink", "duplicate", "copy"
        ]
        
        # Check if user has existing workflow (editing mode vs creation mode)
        existing_workflow = context.get('existing_workflow', {})
        has_existing_nodes = len(existing_workflow.get('nodes', [])) > 0
        
        # If user is giving direct editing commands on existing workflow, skip requirements
        if has_existing_nodes and any(keyword in text.lower() for keyword in editing_keywords):
            return {
                "needs_more_info": False,
                "message": "Processing your workflow editing request.",
                "analysis": "Direct editing command detected, skipping requirement gathering"
            }
        
        if not self.openai_client:
            return {
                "needs_more_info": False,
                "message": "Proceeding with workflow generation based on available information."
            }

        # Check if the request is detailed enough for new workflow creation
        system_prompt = """You are a requirements analyst who determines if enough information has been gathered to create a NEW workflow.

        IMPORTANT: If the user is asking to edit/modify an existing workflow (using words like "remove", "add", "change", "connect", etc.), ALWAYS set needs_more_info to FALSE and let them proceed.

        For NEW workflow creation requests, analyze if you have sufficient information to proceed with workflow generation.

        You have ENOUGH information to proceed if the request includes:
        - Clear workflow purpose/goal
        - Key stakeholders mentioned (who initiates, who approves, who receives)
        - Basic process flow described
        
        You need MORE information only if:
        - The request is extremely vague (like "I want a workflow")
        - No stakeholders are mentioned at all
        - No process steps are described

        IMPORTANT: If the user has provided stakeholders, roles, and basic process steps, set needs_more_info to FALSE and proceed with workflow generation.

        If the user asks you to "just give me a workflow based on what I've given you so far" or similar, ALWAYS set needs_more_info to FALSE.

        Return JSON with:
        - needs_more_info: boolean (false if sufficient info available OR if editing existing workflow)
        - message: your response to the user
        - analysis: brief analysis of information completeness
        """

        try:
            # Include conversation context to make better decisions
            conversation_context = context.get('conversation_history', '')
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User request: '{text}'\nDomain: {context.get('domain', 'general')}\nHas existing workflow: {has_existing_nodes}\nConversation so far: {conversation_context}\n\nDetermine if we have enough information to create a workflow or if more details are needed."}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Override if user explicitly asks to proceed or is editing existing workflow
            if any(phrase in text.lower() for phrase in [
                "just give me", "based on what", "proceed with", "create the workflow", 
                "generate workflow", "move forward", "that's enough"
            ]) or has_existing_nodes:
                result["needs_more_info"] = False
                result["message"] = "I'll create a workflow based on the information you've provided." if not has_existing_nodes else "Processing your workflow modification request."
            
            return result
            
        except Exception as e:
            logger.error(f"Requirement elicitation failed: {e}")
            return {
                "needs_more_info": False,
                "message": "I'll proceed with creating a workflow based on the information available." if not has_existing_nodes else "Processing your workflow editing request.",
                "analysis": "Proceeding due to API error"
            }
