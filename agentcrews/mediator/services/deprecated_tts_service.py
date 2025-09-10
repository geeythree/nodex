import os
import openai
import tempfile
import uuid
from loguru import logger
from datetime import datetime
from typing import Dict, Any

class TextToSpeechService:
    """Service for converting text to speech using OpenAI TTS."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required for TextToSpeechService")
        self.client = openai.OpenAI(api_key=self.api_key)

    async def generate_speech(self, text: str, user_id: str) -> Dict[str, Any]:
        """Generates speech from text and saves it to a temporary file."""
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            filename = f"response_{user_id}_{uuid.uuid4().hex[:8]}.mp3"
            audio_file_path = f"/tmp/{filename}"
            
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
