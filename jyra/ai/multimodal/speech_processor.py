"""
Speech processing module for Jyra
"""

import os
import io
import tempfile
import sys
from typing import Dict, Any, Optional
import speech_recognition as sr
from pydub import AudioSegment
import aiohttp

from jyra.utils.logger import setup_logger

# Set path to FFmpeg binaries
ffmpeg_path = os.path.join(os.path.dirname(
    os.path.dirname(os.path.dirname(__file__))), 'bin')
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]
    # Explicitly set the ffmpeg path for pydub
    AudioSegment.converter = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    AudioSegment.ffmpeg = os.path.join(ffmpeg_path, 'ffmpeg.exe')
    AudioSegment.ffprobe = os.path.join(ffmpeg_path, 'ffprobe.exe')

    logger = setup_logger(__name__)
    logger.info(f"Added FFmpeg path: {ffmpeg_path}")
else:
    logger = setup_logger(__name__)
    logger.warning(f"FFmpeg path not found: {ffmpeg_path}")

logger = setup_logger(__name__)


class SpeechProcessor:
    """
    Class for processing speech to text.
    """

    def __init__(self):
        """
        Initialize the speech processor.
        """
        self.recognizer = sr.Recognizer()
        logger.info("Initialized speech processor")

    async def download_voice(self, file_url: str) -> str:
        """
        Download a voice message from a URL and save it to a temporary file.

        Args:
            file_url (str): URL of the voice message to download

        Returns:
            str: Path to the downloaded voice file
        """
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".ogg")
            temp_path = temp_file.name
            temp_file.close()

            # Download the voice file
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        with open(temp_path, "wb") as f:
                            f.write(await response.read())
                        logger.info(
                            f"Voice message downloaded successfully: {file_url}")
                        return temp_path
                    else:
                        logger.error(
                            f"Error downloading voice message: {response.status}")
                        raise Exception(
                            f"Failed to download voice message: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading voice message: {str(e)}")
            raise

    async def convert_to_wav(self, ogg_path: str) -> str:
        """
        Convert an OGG file to WAV format.

        Args:
            ogg_path (str): Path to the OGG file

        Returns:
            str: Path to the converted WAV file
        """
        try:
            # Create a temporary file for the WAV
            wav_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wav_path = wav_file.name
            wav_file.close()

            # Convert OGG to WAV
            audio = AudioSegment.from_ogg(ogg_path)
            audio.export(wav_path, format="wav")

            logger.info(f"Converted OGG to WAV: {ogg_path} -> {wav_path}")
            return wav_path
        except Exception as e:
            logger.error(f"Error converting OGG to WAV: {str(e)}")
            raise

    async def speech_to_text(self, voice_path: str, language: str = "en-US") -> Dict[str, Any]:
        """
        Convert speech to text.

        Args:
            voice_path (str): Path to the voice file
            language (str): Language code for recognition

        Returns:
            Dict[str, Any]: Recognition results
        """
        try:
            # Check if the file is OGG and convert if needed
            if voice_path.endswith(".ogg"):
                wav_path = await self.convert_to_wav(voice_path)
            else:
                wav_path = voice_path

            # Recognize speech
            with sr.AudioFile(wav_path) as source:
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(
                    audio_data, language=language)

            # Clean up temporary WAV file if it was created
            if wav_path != voice_path and os.path.exists(wav_path):
                os.remove(wav_path)

            logger.info(f"Speech recognition successful: {text}")
            return {
                "success": True,
                "text": text
            }
        except sr.UnknownValueError:
            logger.error("Speech recognition could not understand audio")
            return {
                "success": False,
                "error": "I couldn't understand what was said in that voice message."
            }
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {str(e)}")
            return {
                "success": False,
                "error": "I'm having trouble connecting to the speech recognition service."
            }
        except Exception as e:
            logger.error(f"Error in speech recognition: {str(e)}")
            return {
                "success": False,
                "error": f"An error occurred during speech recognition: {str(e)}"
            }
