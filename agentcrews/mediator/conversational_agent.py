import asyncio
import json
import os
from typing import Dict, Any, List, Optional
from loguru import logger
import openai
from pydantic import BaseModel

class ConversationResponse(BaseModel):
    message: str
    needs_more_info: bool
    suggested_questions: List[str] = []
    collected_requirements: Dict[str, Any] = {}
    ready_for_generation: bool = False

class ConversationalRequirementsAgent:
    """Agent responsible for conversing with users to collect workflow requirements"""
    
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
    
    async def process_requirements_input(
        self, 
        user_input: str, 
        conversation_history: List[Dict[str, str]] = None,
        current_requirements: Dict[str, Any] = None
    ) -> ConversationResponse:
        """Process user input for requirements gathering and respond conversationally"""
        
        if not self.openai_client:
            return ConversationResponse(
                message="I'm having trouble connecting to my AI service. Could you please describe your workflow requirements?",
                needs_more_info=True
            )
        
        # Prepare conversation context
        conversation_context = ""
        if conversation_history:
            recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
            for msg in recent_history:
                role = msg.get('role', 'user')
                content = msg.get('message', '')
                conversation_context += f"{role}: {content}\n"
        
        requirements_context = ""
        if current_requirements:
            requirements_context = f"Current requirements collected: {json.dumps(current_requirements, indent=2)}"
        
        system_prompt = """You are a friendly, professional workflow requirements analyst. Your job is to have a natural conversation with users to understand their workflow needs.

        Key responsibilities:
        1. Ask clarifying questions to understand the workflow completely
        2. Identify the domain (HR, Finance, Healthcare, etc.)
        3. Understand the process steps, stakeholders, and compliance needs
        4. Determine when you have enough information to generate a workflow
        
        Important guidelines:
        - Be conversational and friendly, like a helpful project manager
        - Ask one focused question at a time
        - Build on previous answers
        - Identify compliance requirements (GDPR, HIPAA, SOX, etc.)
        - Understand approval processes and stakeholders
        
        Essential information to collect:
        - Process name/purpose
        - Domain/industry context
        - Key stakeholders (who initiates, approves, receives)
        - Main process steps
        - Compliance/regulatory requirements
        - Data handling needs
        - Approval workflows
        
        Return a JSON object with:
        - message: Your conversational response to the user
        - needs_more_info: boolean indicating if more information is needed
        - suggested_questions: array of follow-up questions you might ask
        - collected_requirements: structured data of what you've learned
        - ready_for_generation: boolean indicating if you have enough info to create a workflow
        """
        
        user_prompt = f"""
        Conversation history:
        {conversation_context}
        
        Current requirements:
        {requirements_context}
        
        Latest user input: "{user_input}"
        
        Respond conversationally and determine what additional information is needed.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            return ConversationResponse(
                message=result.get("message", "Could you tell me more about your workflow?"),
                needs_more_info=result.get("needs_more_info", True),
                suggested_questions=result.get("suggested_questions", []),
                collected_requirements=result.get("collected_requirements", {}),
                ready_for_generation=result.get("ready_for_generation", False)
            )
            
        except Exception as e:
            logger.error(f"Conversational agent failed: {str(e)}")
            return self._fallback_response(user_input)
    
    def _fallback_response(self, user_input: str) -> ConversationResponse:
        """Fallback response when AI is unavailable"""
        return ConversationResponse(
            message="I understand you want to create a workflow. Could you tell me more about the process you'd like to automate? For example, what domain is this for (HR, Finance, etc.) and what are the main steps involved?",
            needs_more_info=True,
            suggested_questions=[
                "What domain/industry is this workflow for?",
                "Who are the main stakeholders involved?",
                "What are the key steps in this process?"
            ]
        )
    
    async def generate_workflow_summary(self, requirements: Dict[str, Any]) -> str:
        """Generate a summary of the workflow that will be created"""
        
        if not self.openai_client:
            return "Based on your requirements, I'll create a workflow with the specified steps and stakeholders."
        
        system_prompt = """You are a workflow architect. Given the collected requirements, provide a clear, concise summary of the workflow you will create. 

        Focus on:
        - Main process flow
        - Key stakeholders and their roles
        - Compliance considerations
        - Expected outcomes
        
        Keep it conversational and reassuring - let the user know you understand their needs."""
        
        user_prompt = f"Requirements: {json.dumps(requirements, indent=2)}\n\nProvide a summary of the workflow I'll create."
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return "Based on your requirements, I'll create a workflow that addresses your process needs with appropriate compliance measures."
