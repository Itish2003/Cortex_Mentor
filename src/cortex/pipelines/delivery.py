import asyncio
from cortex.pipelines.processors import Processor
import logging
from redis.asyncio import Redis
from google.cloud import texttospeech
from cortex.core.config import Settings
import base64
import json

logger = logging.getLogger(__name__)

class AudioDeliveryProcessor(Processor):
    """
    Converts text to audio using Google Cloud Text-to-Speech and publishes it to a Redis channel.
    """
    def __init__(self, redis: Redis):
        self.redis = redis
        self.settings = Settings()
        self.tts_client = texttospeech.TextToSpeechClient()

    async def process(self, data: dict, context: dict) -> dict:
        final_insight = data.get("final_insight")
        if not final_insight:
            logger.warning("No final insight found to convert to audio.")
            return data

        logger.info("Converting final insight to audio using Google Cloud Text-to-Speech...")
        try:
            synthesis_input = texttospeech.SynthesisInput(text=final_insight)
            voice_params = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name=self.settings.tts_voice_name
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )

            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=voice_params,
                audio_config=audio_config
            )

            audio_data = response.audio_content

            if audio_data:
                logger.info("Publishing audio data to Redis 'insights_channel'...")
                
                # Encode audio to base64 string
                audio_b64 = base64.b64encode(audio_data).decode('utf-8')
                
                message = {
                    "type": "insight",
                    "text": final_insight,
                    "audio": audio_b64
                }
                
                await self.redis.publish("insights_channel", json.dumps(message))
                logger.info("Audio data published successfully.")
            else:
                logger.warning("Google Cloud Text-to-Speech returned no audio data.")

        except Exception as e:
            logger.error(f"Error during audio generation or publishing: {e}", exc_info=True)

        return data
 