import asyncio
import os
from typing import Dict, Any, Optional, Callable
from loguru import logger
import json
from datetime import datetime

from pipecat.frames.frames import (
    Frame, AudioRawFrame, TextFrame, TranscriptionFrame, 
    TTSStartedFrame, TTSStoppedFrame, UserStartedSpeakingFrame, 
    UserStoppedSpeakingFrame
)
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask, PipelineParams
from pipecat.services.openai import OpenAITTSService, OpenAILLMService
from pipecat.services.whisper import WhisperSTTService
from pipecat.transports.services.daily import DailyTransport, DailyParams
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext

class PipecatVoiceHandler:
    """Pipecat-based voice handler for real-time conversational AI"""
    
    def __init__(self):
        self.transport = None
        self.pipeline_task = None
        self.conversation_callback: Optional[Callable] = None
        self.session_callbacks: Dict[str, Callable] = {}
        
    async def initialize_session(self, session_id: str, room_url: str, token: str) -> Dict[str, Any]:
        """Initialize a new Pipecat session for voice interaction"""
        try:
            # Configure services
            stt_service = WhisperSTTService(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="whisper-1"
            )
            
            tts_service = OpenAITTSService(
                api_key=os.getenv("OPENAI_API_KEY"),
                voice="alloy"  # OpenAI TTS voice
            )
            
            # Configure transport
            transport = DailyTransport(
                room_url=room_url,
                token=token,
                bot_name="SecureAI Assistant",
                params=DailyParams(
                    audio_out_enabled=True,
                    audio_in_enabled=True,
                    transcription_enabled=True,
                    vad_enabled=True,
                    vad_analyzer=DailyParams.VADAnalyzer.SILERO
                )
            )
            
            # Create conversation context
            context = OpenAILLMContext()
            
            # Create LLM service for conversation
            llm_service = OpenAILLMService(
                api_key=os.getenv("OPENAI_API_KEY"),
                model="gpt-4-turbo"
            )
            
            # Create pipeline
            pipeline = Pipeline([
                transport.input(),
                stt_service,
                context.user(),
                llm_service,
                tts_service,
                transport.output(),
                context.assistant()
            ])
            
            # Create and store task
            task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    allow_interruptions=True,
                    enable_metrics=True,
                    enable_usage_metrics=True
                )
            )
            
            # Set up event handlers
            self._setup_event_handlers(transport, session_id)
            
            # Store session components
            self.session_callbacks[session_id] = {
                'transport': transport,
                'task': task,
                'context': context
            }
            
            return {
                "success": True,
                "session_id": session_id,
                "room_url": room_url
            }
            
        except Exception as e:
            logger.error(f"Failed to initialize Pipecat session: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _setup_event_handlers(self, transport: DailyTransport, session_id: str):
        """Set up event handlers for the transport"""
        
        @transport.event_handler("on_first_participant_joined")
        async def on_participant_joined(transport, participant):
            logger.info(f"Participant joined session {session_id}: {participant}")
            # Send initial greeting
            await transport.send_message("Hello! I'm your SecureAI workflow assistant. How can I help you today?")
        
        @transport.event_handler("on_participant_left")
        async def on_participant_left(transport, participant, reason):
            logger.info(f"Participant left session {session_id}: {participant}, reason: {reason}")
        
        @transport.event_handler("on_call_state_updated")
        async def on_call_state_updated(transport, state):
            logger.info(f"Call state updated for session {session_id}: {state}")
    
    async def start_session(self, session_id: str) -> bool:
        """Start the Pipecat pipeline for a session"""
        try:
            if session_id not in self.session_callbacks:
                logger.error(f"Session {session_id} not found")
                return False
            
            session_data = self.session_callbacks[session_id]
            task = session_data['task']
            
            # Start the pipeline
            runner = PipelineRunner()
            await runner.run(task)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start session {session_id}: {str(e)}")
            return False
    
    async def send_message_to_session(self, session_id: str, message: str) -> bool:
        """Send a text message to a specific session"""
        try:
            if session_id not in self.session_callbacks:
                logger.error(f"Session {session_id} not found")
                return False
            
            session_data = self.session_callbacks[session_id]
            transport = session_data['transport']
            
            # Send message through transport
            await transport.send_message(message)
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to session {session_id}: {str(e)}")
            return False
    
    async def inject_workflow_context(self, session_id: str, workflow_data: Dict[str, Any]) -> bool:
        """Inject workflow context into the conversation"""
        try:
            if session_id not in self.session_callbacks:
                logger.error(f"Session {session_id} not found")
                return False
            
            session_data = self.session_callbacks[session_id]
            context = session_data['context']
            
            # Add workflow context to the conversation
            workflow_summary = f"Current workflow has {len(workflow_data.get('nodes', []))} nodes and {len(workflow_data.get('edges', []))} connections."
            
            context_frame = TextFrame(
                text=f"[SYSTEM] Workflow updated: {workflow_summary}"
            )
            
            # Add to context
            await context.add_message(context_frame)
            return True
            
        except Exception as e:
            logger.error(f"Failed to inject workflow context: {str(e)}")
            return False
    
    async def end_session(self, session_id: str) -> bool:
        """End a Pipecat session and cleanup resources"""
        try:
            if session_id not in self.session_callbacks:
                logger.warning(f"Session {session_id} not found for cleanup")
                return False
            
            session_data = self.session_callbacks[session_id]
            transport = session_data['transport']
            
            # Leave the room and cleanup
            await transport.cleanup()
            
            # Remove from callbacks
            del self.session_callbacks[session_id]
            
            logger.info(f"Session {session_id} ended and cleaned up")
            return True
            
        except Exception as e:
            logger.error(f"Failed to end session {session_id}: {str(e)}")
            return False
    
    def set_conversation_callback(self, callback: Callable):
        """Set callback for conversation events"""
        self.conversation_callback = callback
    
    async def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a session"""
        try:
            if session_id not in self.session_callbacks:
                return None
            
            session_data = self.session_callbacks[session_id]
            task = session_data['task']
            
            # Get metrics from the task
            metrics = await task.get_metrics()
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to get metrics for session {session_id}: {str(e)}")
            return None

    async def process_voice_input(self, audio_file_path: str, user_id: str) -> Dict[str, Any]:
        """Process voice input using OpenAI Whisper for transcription"""
        try:
            import openai
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Transcribe audio using Whisper
            with open(audio_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            logger.info(f"Voice transcription for user {user_id}: {transcript}")
            
            return {
                "success": True,
                "content": transcript,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to process voice input: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "user_id": user_id
            }
    
    async def generate_agent_response(self, text: str, user_id: str) -> Dict[str, Any]:
        """Generate agent response with OpenAI TTS"""
        try:
            import openai
            import tempfile
            import uuid
            
            # Initialize OpenAI client
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Generate TTS audio
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Create unique filename
            filename = f"response_{user_id}_{uuid.uuid4().hex[:8]}.mp3"
            audio_file_path = f"/tmp/{filename}"
            
            # Save audio to file
            response.stream_to_file(audio_file_path)
            
            logger.info(f"Generated TTS response for user {user_id}: {text[:50]}...")
            
            return {
                "success": True,
                "audio_file_path": audio_file_path,
                "filename": filename,
                "audio_url": f"/api/audio/{filename}",
                "text": text,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate agent response: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": text,
                "user_id": user_id
            }
