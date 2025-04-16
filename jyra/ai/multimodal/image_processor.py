"""
Image processing module for Jyra
"""

import os
import io
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image
import aiohttp
import json

from jyra.utils.config import GEMINI_API_KEY
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class ImageProcessor:
    """
    Class for processing and analyzing images.
    """

    def __init__(self):
        """
        Initialize the image processor.
        """
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        logger.info("Initialized image processor")

    async def process_image(self, image_path: str, prompt: Optional[str] = None) -> str:
        """
        Process an image and generate a description or response to a prompt.

        Args:
            image_path (str): Path to the image file
            prompt (Optional[str]): Optional prompt to guide the image analysis

        Returns:
            str: Description or response based on the image
        """
        try:
            # Read the image and convert to base64
            with open(image_path, "rb") as image_file:
                image_bytes = image_file.read()

            # Process the image with Gemini
            result = await self._analyze_with_gemini(image_bytes, prompt)
            logger.info(f"Image processed successfully: {image_path}")
            return result
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return "I had trouble processing that image. Could you try another one?"

    async def download_image(self, file_url: str) -> str:
        """
        Download an image from a URL and save it to a temporary file.

        Args:
            file_url (str): URL of the image to download

        Returns:
            str: Path to the downloaded image
        """
        try:
            # Create a temporary file
            temp_file = tempfile.NamedTemporaryFile(
                delete=False, suffix=".jpg")
            temp_path = temp_file.name
            temp_file.close()

            # Download the image
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        with open(temp_path, "wb") as f:
                            f.write(await response.read())
                        logger.info(
                            f"Image downloaded successfully: {file_url}")
                        return temp_path
                    else:
                        logger.error(
                            f"Error downloading image: {response.status}")
                        raise Exception(
                            f"Failed to download image: {response.status}")
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            raise

    async def _analyze_with_gemini(self, image_bytes: bytes, prompt: Optional[str] = None) -> str:
        """
        Analyze an image using Gemini.

        Args:
            image_bytes (bytes): The image data
            prompt (Optional[str]): Optional prompt to guide the analysis

        Returns:
            str: Analysis result
        """
        import base64

        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        # Default prompt if none provided
        if not prompt:
            prompt = "Describe this image in detail. What do you see?"

        # Prepare the request payload
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 800,
                "topP": 0.95,
                "topK": 40
            }
        }

        # Make the API request
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()

                    # Extract the response text
                    if "candidates" in result and len(result["candidates"]) > 0:
                        candidate = result["candidates"][0]
                        if "content" in candidate and "parts" in candidate["content"]:
                            parts = candidate["content"]["parts"]
                            if len(parts) > 0 and "text" in parts[0]:
                                response_text = parts[0]["text"]
                                return response_text

                    logger.error(f"Unexpected response format: {result}")
                    return "I received a response but couldn't understand it. Could you try again with a different image?"
                else:
                    error_text = await response.text()
                    logger.error(f"API error: {response.status}, {error_text}")
                    return f"I'm having trouble analyzing that image right now (Error {response.status}). Please try again later."
