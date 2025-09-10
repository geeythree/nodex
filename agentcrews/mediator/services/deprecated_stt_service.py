import os
import openai
from loguru import logger
from datetime import datetime
from typing import Dict, Any

class SpeechToTextService:
    """Service for converting speech to text using OpenAI Whisper."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required for SpeechToTextService")
        self.client = openai.OpenAI(api_key=self.api_key)

    async def transcribe_audio(self, audio_file_path: str, user_id: str) -> Dict[str, Any]:
        """Transcribes an audio file using the Whisper API."""
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
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
