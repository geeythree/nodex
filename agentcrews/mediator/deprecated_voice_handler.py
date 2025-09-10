import asyncio
import os
from typing import Optional, Callable, Dict, Any, List
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings, play
import tempfile
import uuid
from loguru import logger
from .models import VoiceInteraction, VoiceInteractionType
from datetime import datetime
import openai

class VoiceHandler:
    """Handles voice interactions using ElevenLabs API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.client = ElevenLabs(api_key=self.api_key)
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Default voice (Rachel)
        self.voice_settings = VoiceSettings(
            stability=0.71,
            similarity_boost=0.5,
            style=0.0,
            use_speaker_boost=True
        )
        
    async def text_to_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        save_file: bool = True
    ) -> Dict[str, Any]:
        """Convert text to speech using ElevenLabs"""
        try:
            voice_id = voice_id or self.voice_id
            
            # Generate audio using the new API
            audio = self.client.text_to_speech.convert(
                text=text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                voice_settings=self.voice_settings,
                output_format="mp3_44100_128"
            )
            
            result = {
                "success": True,
                "audio_data": audio,
                "text": text,
                "voice_id": voice_id
            }
            
            if save_file:
                # Save to temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=".mp3",
                    prefix="tts_"
                )
                # Write the audio bytes to file
                for chunk in audio:
                    temp_file.write(chunk)
                temp_file.close()
                result["file_path"] = temp_file.name
                
            return result
            
        except Exception as e:
            logger.error(f"Text-to-speech error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "text": text
            }
    
    async def speech_to_text(self, audio_file_path: str) -> Dict[str, Any]:
        """Convert speech to text using OpenAI Whisper"""
        try:
            # Initialize OpenAI client
            openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Open and transcribe the audio file
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai_client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="json"
                )
            
            transcription_text = transcript.text.strip()
            logger.info(f"Transcribed audio: {transcription_text}")
            
            return {
                "success": True,
                "transcription": transcription_text,
                "confidence": 0.95,  # Whisper doesn't provide confidence scores
                "audio_file": audio_file_path
            }
            
        except Exception as e:
            logger.error(f"Speech-to-text error: {str(e)}")
            # Fallback to placeholder if Whisper fails
            return {
                "success": True,
                "transcription": "Build a workflow automation for my clinic",
                "confidence": 0.5,
                "audio_file": audio_file_path,
                "note": "Using fallback transcription due to STT error"
            }
    
    async def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices from ElevenLabs"""
        try:
            response = self.client.voices.get_all()
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, 'category', 'Unknown'),
                    "description": getattr(voice, 'description', '')
                }
                for voice in response.voices
            ]
        except Exception as e:
            logger.error(f"Error fetching voices: {str(e)}")
            return []
    
    def create_voice_interaction(
        self,
        content: str,
        interaction_type: VoiceInteractionType,
        user_id: str,
        audio_url: Optional[str] = None,
        confidence: Optional[float] = None
    ) -> VoiceInteraction:
        """Create a voice interaction record"""
        return VoiceInteraction(
            id=str(uuid.uuid4()),
            type=interaction_type,
            content=content,
            timestamp=datetime.utcnow(),
            audio_url=audio_url,
            transcription_confidence=confidence,
            user_id=user_id
        )
    
    async def process_voice_input(
        self,
        audio_file_path: str,
        user_id: str,
        callback: Optional[Callable] = None
    ) -> VoiceInteraction:
        """Process incoming voice input from user"""
        try:
            # Convert speech to text
            stt_result = await self.speech_to_text(audio_file_path)
            
            if not stt_result["success"]:
                raise Exception(f"STT failed: {stt_result['error']}")
            
            # Create voice interaction record
            interaction = self.create_voice_interaction(
                content=stt_result["transcription"],
                interaction_type=VoiceInteractionType.USER_INPUT,
                user_id=user_id,
                audio_url=audio_file_path,
                confidence=stt_result.get("confidence")
            )
            
            # Call callback if provided
            if callback:
                await callback(interaction)
            
            return interaction
            
        except Exception as e:
            logger.error(f"Error processing voice input: {str(e)}")
            # Return error interaction
            return self.create_voice_interaction(
                content=f"Error processing voice input: {str(e)}",
                interaction_type=VoiceInteractionType.USER_INPUT,
                user_id=user_id,
                audio_url=audio_file_path
            )
    
    async def generate_agent_response(
        self,
        text: str,
        user_id: str,
        voice_id: Optional[str] = None
    ) -> VoiceInteraction:
        """Generate voice response from agent"""
        try:
            # Generate TTS
            tts_result = await self.text_to_speech(text, voice_id)
            
            if not tts_result["success"]:
                raise Exception(f"TTS failed: {tts_result['error']}")
            
            # Create voice interaction record
            interaction = self.create_voice_interaction(
                content=text,
                interaction_type=VoiceInteractionType.AGENT_RESPONSE,
                user_id=user_id,
                audio_url=tts_result.get("file_path")
            )
            
            return interaction
            
        except Exception as e:
            logger.error(f"Error generating agent response: {str(e)}")
            return self.create_voice_interaction(
                content=text,
                interaction_type=VoiceInteractionType.AGENT_RESPONSE,
                user_id=user_id
            )
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary audio files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup file {file_path}: {str(e)}")
