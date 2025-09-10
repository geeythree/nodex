import asyncio
import json
import os
import uuid
from typing import Dict, Any, List, Optional
from loguru import logger
import openai
from pydantic import BaseModel

class GraphEditResponse(BaseModel):
    success: bool
    message: str
    updated_workflow: Dict[str, Any]
    changes_made: List[str] = []
    error: Optional[str] = None

class GraphEditingAgent:
    """Agent responsible for editing existing workflows based on user commands"""
    
    def __init__(self):
        self.openai_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not found in environment variables")
            return
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
    
    async def edit_workflow(
        self, 
        user_command: str, 
        current_workflow: Dict[str, Any],
        extracted_entities: Dict[str, Any] = None
    ) -> GraphEditResponse:
        """Edit workflow based on user command"""
        
        if not self.openai_client:
            return self._fallback_edit(user_command, current_workflow)
        
        # Prepare context
        entities_context = ""
        if extracted_entities:
            entities_context = f"Extracted entities: {json.dumps(extracted_entities)}"
        
        system_prompt = """You are a workflow graph editor. You receive editing commands and modify existing workflows accordingly.

        Common commands you handle:
        - "add a [type] node called [name]" - Add new nodes
        - "remove the [name] node" - Remove existing nodes
        - "connect [node1] to [node2]" - Add edges between nodes
        - "disconnect [node1] from [node2]" - Remove edges
        - "change [node] label to [new_label]" - Modify node properties
        - "move [node] after [other_node]" - Reposition nodes

        Rules:
        1. Preserve existing node IDs unless explicitly changing them
        2. Generate new IDs for new nodes using format: [type]_[random_string]
        3. Maintain workflow integrity (don't create orphaned nodes)
        4. Respect compliance nodes (locked=true) - warn if user tries to modify them
        5. Provide clear feedback about what was changed

        Return JSON with:
        - success: boolean
        - message: conversational response to user
        - updated_workflow: complete modified workflow
        - changes_made: list of specific changes
        - error: error message if something went wrong
        """
        
        user_prompt = f"""
        Current workflow:
        {json.dumps(current_workflow, indent=2)}
        
        {entities_context}
        
        User command: "{user_command}"
        
        Execute this command and return the updated workflow.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Ensure changes_made is a list of strings
            changes_made = result.get("changes_made", [])
            if changes_made and isinstance(changes_made[0], dict):
                # Convert dict entries to strings
                changes_made = [str(change) for change in changes_made]
            
            return GraphEditResponse(
                success=result.get("success", False),
                message=result.get("message", "Workflow updated"),
                updated_workflow=result.get("updated_workflow", current_workflow),
                changes_made=changes_made,
                error=result.get("error")
            )
            
        except Exception as e:
            logger.error(f"Graph editing failed: {str(e)}")
            return GraphEditResponse(
                success=False,
                message="I encountered an error while editing the workflow. Please try again.",
                updated_workflow=current_workflow,
                error=str(e)
            )
    
    def _fallback_edit(self, user_command: str, current_workflow: Dict[str, Any]) -> GraphEditResponse:
        """Fallback editing using simple pattern matching"""
        command_lower = user_command.lower()
        nodes = current_workflow.get("nodes", [])
        edges = current_workflow.get("edges", [])
        changes_made = []
        
        try:
            # Simple add node pattern
            if "add" in command_lower and "node" in command_lower:
                # Extract node type and name
                node_type = "process"  # default
                if "input" in command_lower:
                    node_type = "input"
                elif "output" in command_lower:
                    node_type = "output"
                elif "approval" in command_lower:
                    node_type = "approval"
                
                # Generate new node
                new_node = {
                    "id": f"{node_type}_{uuid.uuid4().hex[:8]}",
                    "type": node_type,
                    "data": {
                        "label": f"New {node_type.title()} Node",
                        "description": f"Added via command: {user_command}",
                        "locked": False,
                        "compliance_type": None
                    },
                    "position": {
                        "x": 100 + len(nodes) * 200,
                        "y": 200
                    }
                }
                
                nodes.append(new_node)
                changes_made.append(f"Added {node_type} node")
                
                return GraphEditResponse(
                    success=True,
                    message=f"I've added a new {node_type} node to your workflow.",
                    updated_workflow={"nodes": nodes, "edges": edges},
                    changes_made=changes_made
                )
            
            # Simple remove node pattern
            elif "remove" in command_lower or "delete" in command_lower:
                # This is more complex - would need better NLP to identify which node
                return GraphEditResponse(
                    success=False,
                    message="I need more specific information about which node to remove. Could you specify the node name or ID?",
                    updated_workflow=current_workflow,
                    error="Insufficient information for node removal"
                )
            
            else:
                return GraphEditResponse(
                    success=False,
                    message="I didn't understand that editing command. Could you try rephrasing it?",
                    updated_workflow=current_workflow,
                    error="Command not recognized"
                )
                
        except Exception as e:
            return GraphEditResponse(
                success=False,
                message="I encountered an error while editing the workflow.",
                updated_workflow=current_workflow,
                error=str(e)
            )
