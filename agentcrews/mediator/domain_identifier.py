import os
from typing import Literal
from loguru import logger
import openai
from pydantic import BaseModel, Field

# Define the structure for the domain classification output
class DomainClassification(BaseModel):
    domain: Literal["hr", "sales", "finance", "operations", "it", "general"] = Field(
        ..., 
        description="The business domain classified from the user input."
    )
    confidence: float = Field(
        ..., 
        description="The confidence score of the classification, between 0 and 1."
    )
    reasoning: str = Field(
        ..., 
        description="A brief explanation for the domain classification."
    )

class DomainIdentificationAgent:
    """An agent that identifies the business domain from user input."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required for DomainIdentificationAgent")
        self.client = openai.AsyncOpenAI(api_key=self.api_key)

    async def identify_domain(self, text: str) -> DomainClassification:
        """Identifies the business domain for a given text using an LLM call."""
        system_prompt = """You are an expert at identifying the business domain from a user's request.
        Classify the user's input into one of the following domains:
        - hr: Human Resources, employee onboarding, performance reviews, etc.
        - sales: Lead management, customer relationship management, sales pipelines, etc.
        - finance: Expense reports, invoicing, budget approvals, etc.
        - operations: Supply chain, logistics, internal processes, etc.
        - it: Incident management, tech support, asset tracking, etc.
        - general: If the domain is not specific or cannot be determined.

        Return a JSON object with 'domain', 'confidence' (a float between 0.0 and 1.0), and 'reasoning'.
        """
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f'User request: "{text}"'}
                ],
                response_format={"type": "json_object"}
            )
            result = response.choices[0].message.content
            classification = DomainClassification.model_validate_json(result)
            logger.info(f"Domain identified: {classification.domain} (Confidence: {classification.confidence})")
            return classification
        except Exception as e:
            logger.error(f"Domain identification failed: {e}")
            return DomainClassification(
                domain="general",
                confidence=0.5,
                reasoning=f"Fell back to general due to an error: {e}"
            )
