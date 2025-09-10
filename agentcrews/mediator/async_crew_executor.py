"""
Async executor for CrewAI crews
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional
import logging
from crewai import Crew

logger = logging.getLogger(__name__)

class AsyncCrewExecutor:
    """Execute CrewAI crews asynchronously to avoid blocking the event loop"""
    
    def __init__(self, max_workers: int = 2):
        """
        Initialize the async executor
        
        Args:
            max_workers: Maximum number of threads for crew execution
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
    
    async def execute_crew(self, crew: Crew, inputs: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a CrewAI crew asynchronously
        
        Args:
            crew: The CrewAI crew to execute
            inputs: Optional inputs for the crew
            
        Returns:
            The crew execution result
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Run the synchronous crew.kickoff() in a thread pool
            if inputs:
                result = await loop.run_in_executor(
                    self.executor,
                    lambda: crew.kickoff(inputs=inputs)
                )
            else:
                result = await loop.run_in_executor(
                    self.executor,
                    crew.kickoff
                )
            
            logger.info("Crew execution completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Crew execution failed: {str(e)}")
            raise
    
    def __del__(self):
        """Cleanup the executor on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)