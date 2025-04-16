"""
Text-to-speech module for Jyra
"""

import os
import io
import tempfile
import sys
from typing import Dict, Any, Optional
from gtts import gTTS
import aiohttp

from jyra.utils.logger import setup_logger

# Set path to FFmpeg binaries
ffmpeg_path = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))), 'bin')
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    logger = setup_logger(__name__)
    logger.info(f"Added FFmpeg path: {ffmpeg_path}")
else:
    logger = setup_logger(__name__)
    logger.warning(f"FFmpeg path not found: {ffmpeg_path}")


class TTSProcessor:
    """
    Class for converting text to speech.
    """

    def __init__(self):
        """
        Initialize the TTS processor.
        """
        logger.info("Initialized TTS processor")

    async def text_to_speech(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Convert text to speech.

        Args:
            text (str): Text to convert to speech
            language (str): Language code for TTS

        Returns:
            Dict[str, Any]: Path to the generated audio file
        """
        try:
            # Create a temporary file for the audio
            audio_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".mp3")
            audio_path = audio_file.name
            audio_file.close()

            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            tts.save(audio_path)

            logger.info(f"Text-to-speech successful: {audio_path}")
            return {
                "success": True,
                "file_path": audio_path
            }
        except Exception as e:
            logger.error(f"Error in text-to-speech: {str(e)}")
            return {
                "success": False,
                "error": f"An error occurred during text-to-speech conversion: {str(e)}"
            }

    def cleanup_file(self, file_path: str) -> None:
        """
        Clean up a temporary file.

        Args:
            file_path (str): Path to the file to clean up
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
        except Exception as e:
            logger.error(f"Error cleaning up file: {str(e)}")
