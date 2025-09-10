import asyncio
import json
import os
from typing import Dict, Any, Literal
from loguru import logger
import openai
from pydantic import BaseModel

class IntentClassification(BaseModel):
    intent_type: Literal["edit_workflow", "requirements_gathering", "project_specification"]
    confidence: float
    reasoning: str
    extracted_entities: Dict[str, Any] = {}

class IntentClassificationAgent:
    """Agent responsible for classifying user intent and routing to appropriate handlers"""
    
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
    
    async def classify_intent(self, user_input: str, conversation_context: list = None, current_workflow_exists: bool = False) -> IntentClassification:
        """Classify user intent based on input and context"""
        
        if not self.openai_client:
            # Fallback classification
            return IntentClassification(
                intent_type="requirements_gathering",
                confidence=0.5,
                reasoning="OpenAI client not available, defaulting to requirements gathering"
            )
        
        # Build context for the classifier
        context_info = ""
        if current_workflow_exists:
            context_info += "Current workflow exists. "
        if conversation_context:
            recent_messages = conversation_context[-3:] if len(conversation_context) > 3 else conversation_context
            context_info += f"Recent conversation: {json.dumps(recent_messages)}"
        
        system_prompt = """You are an intent classification agent for a workflow builder system. 
        
        Classify user input into one of these categories:

        1. **edit_workflow**: User wants to modify an existing workflow
           - Examples: "add a node", "remove the approval step", "connect input to process", "change the label"
           - Keywords: add, remove, delete, connect, disconnect, modify, change, update, edit
           
        2. **requirements_gathering**: User is responding to questions or providing partial information
           - Examples: "It's for employee onboarding", "Yes, we need approval", "The manager should review it"
           - Context: Usually follows a question from the system
           
        3. **project_specification**: User is describing a new workflow or process from scratch
           - Examples: "I need a workflow for expense approval", "Create a process for customer onboarding"
           - Keywords: create, build, need, want, workflow for, process for

        Return a JSON object with:
        - intent_type: one of the three categories
        - confidence: float between 0-1
        - reasoning: brief explanation
        - extracted_entities: a dictionary of relevant entities found (e.g., {{"action": "add", "node_type": "approval"}})
        """
        
        user_prompt = f"""
        Context: {context_info}
        User input: "{user_input}"
        
        Classify this intent and extract relevant entities.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return IntentClassification(
                intent_type=result.get("intent_type", "requirements_gathering"),
                confidence=result.get("confidence", 0.5),
                reasoning=result.get("reasoning", ""),
                extracted_entities=result.get("extracted_entities", {})
            )
            
        except Exception as e:
            logger.error(f"Intent classification failed: {str(e)}")
            # Fallback logic based on keywords
            return self._fallback_classification(user_input, current_workflow_exists)
    
    def _fallback_classification(self, user_input: str, current_workflow_exists: bool) -> IntentClassification:
        """Fallback classification using simple keyword matching"""
        user_lower = user_input.lower()
        
        # Edit workflow keywords
        edit_keywords = ["add", "remove", "delete", "connect", "disconnect", "modify", "change", "update", "edit"]
        if any(keyword in user_lower for keyword in edit_keywords) and current_workflow_exists:
            return IntentClassification(
                intent_type="edit_workflow",
                confidence=0.7,
                reasoning="Contains editing keywords and workflow exists"
            )
        
        # Project specification keywords
        project_keywords = ["create", "build", "need", "want", "workflow for", "process for"]
        if any(keyword in user_lower for keyword in project_keywords):
            return IntentClassification(
                intent_type="project_specification",
                confidence=0.6,
                reasoning="Contains project creation keywords"
            )
        
        # Default to requirements gathering
        return IntentClassification(
            intent_type="requirements_gathering",
            confidence=0.5,
            reasoning="Default classification - no clear indicators"
        )
