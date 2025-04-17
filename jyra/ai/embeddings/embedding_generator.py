"""
Embedding generator for Jyra.

This module generates vector embeddings for text using various embedding models.
"""

import aiohttp
import numpy as np
from typing import List, Dict, Any, Optional, Union
import json

from jyra.utils.config import GEMINI_API_KEY, OPENAI_API_KEY, ENABLE_OPENAI
from jyra.utils.logger import setup_logger
from jyra.utils.exceptions import AIModelException, APIRateLimitException, APIAuthenticationException

logger = setup_logger(__name__)


class EmbeddingGenerator:
    """
    Class for generating vector embeddings for text.
    """

    def __init__(self, model_name: str = "gemini-embedding"):
        """
        Initialize the embedding generator.

        Args:
            model_name (str): The name of the embedding model to use
        """
        self.model_name = model_name

        # Set up API endpoints based on the model
        if "gemini" in model_name.lower():
            self.api_url = f"https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent?key={GEMINI_API_KEY}"
            self.provider = "Google"
        elif "openai" in model_name.lower() or "ada" in model_name.lower():
            self.api_url = "https://api.openai.com/v1/embeddings"
            self.provider = "OpenAI"
        else:
            # Default to Gemini
            self.api_url = f"https://generativelanguage.googleapis.com/v1/models/embedding-001:embedContent?key={GEMINI_API_KEY}"
            self.provider = "Google"
            self.model_name = "gemini-embedding"

        logger.info(
            f"Initialized embedding generator with model: {self.model_name}")

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding for the given text.

        Args:
            text (str): The text to generate an embedding for

        Returns:
            List[float]: The vector embedding

        Raises:
            AIModelException: If there's an error with the model
            APIRateLimitException: If the API rate limit is reached
            APIAuthenticationException: If there's an authentication error
        """
        if not text or not text.strip():
            # Return a zero vector for empty text
            return [0.0] * 768  # Default dimension for most embedding models

        try:
            if self.provider == "Google":
                return await self._generate_gemini_embedding(text)
            elif self.provider == "OpenAI" and ENABLE_OPENAI:
                return await self._generate_openai_embedding(text)
            else:
                # Fall back to Gemini if OpenAI is disabled
                return await self._generate_gemini_embedding(text)

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise AIModelException(
                self.model_name, f"Error generating embedding: {str(e)}")

    async def _generate_gemini_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding using Gemini's embedding model.

        Args:
            text (str): The text to generate an embedding for

        Returns:
            List[float]: The vector embedding
        """
        try:
            # Prepare the API request
            payload = {
                "model": "embedding-001",
                "content": {
                    "parts": [
                        {"text": text}
                    ]
                }
            }

            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract the embedding
                        if "embedding" in result:
                            embedding = result["embedding"]
                            return embedding

                        logger.error(f"Unexpected response format: {result}")
                        raise AIModelException(
                            self.model_name, "Unexpected response format")
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error: {response.status}, {error_text}")

                        try:
                            error_data = json.loads(error_text)
                            if "error" in error_data:
                                error_code = error_data['error'].get('code', 0)
                                error_message = error_data['error'].get(
                                    'message', 'Unknown error')

                                # Handle specific error codes
                                if error_code == 429:
                                    raise APIRateLimitException(
                                        "Gemini", error_message)
                                elif error_code in (401, 403):
                                    raise APIAuthenticationException(
                                        "Gemini", error_message)
                                else:
                                    raise AIModelException(
                                        self.model_name, f"API error: {error_message}")
                        except json.JSONDecodeError:
                            # If we can't parse the error as JSON, use the status code
                            if response.status == 429:
                                raise APIRateLimitException(
                                    "Gemini", f"Rate limit exceeded (HTTP {response.status})")
                            elif response.status in (401, 403):
                                raise APIAuthenticationException(
                                    "Gemini", f"Authentication error (HTTP {response.status})")

                        # Default error if no specific error was raised
                        raise AIModelException(
                            self.model_name, f"API error: HTTP {response.status}")

        except (AIModelException, APIRateLimitException, APIAuthenticationException):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error generating Gemini embedding: {str(e)}")
            raise AIModelException(
                self.model_name, f"Unexpected error: {str(e)}")

    async def _generate_openai_embedding(self, text: str) -> List[float]:
        """
        Generate a vector embedding using OpenAI's embedding model.

        Args:
            text (str): The text to generate an embedding for

        Returns:
            List[float]: The vector embedding
        """
        if not ENABLE_OPENAI or not OPENAI_API_KEY:
            raise AIModelException(
                self.model_name, "OpenAI is disabled or API key is not set")

        try:
            # Prepare the API request
            payload = {
                "model": "text-embedding-3-small",  # Use the latest embedding model
                "input": text
            }

            headers = {
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            }

            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()

                        # Extract the embedding
                        if "data" in result and len(result["data"]) > 0 and "embedding" in result["data"][0]:
                            embedding = result["data"][0]["embedding"]
                            return embedding

                        logger.error(f"Unexpected response format: {result}")
                        raise AIModelException(
                            self.model_name, "Unexpected response format")
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error: {response.status}, {error_text}")

                        try:
                            error_data = json.loads(error_text)
                            error_message = error_data.get(
                                "error", {}).get("message", "Unknown error")
                            error_type = error_data.get(
                                "error", {}).get("type", "")

                            # Handle specific error types
                            if response.status == 429 or "rate_limit" in error_type:
                                raise APIRateLimitException(
                                    "OpenAI", error_message)
                            elif response.status in (401, 403) or "authentication" in error_type:
                                raise APIAuthenticationException(
                                    "OpenAI", error_message)
                            else:
                                raise AIModelException(
                                    self.model_name, f"API error: {error_message}")
                        except json.JSONDecodeError:
                            # If we can't parse the error as JSON, use the status code
                            if response.status == 429:
                                raise APIRateLimitException(
                                    "OpenAI", f"Rate limit exceeded (HTTP {response.status})")
                            elif response.status in (401, 403):
                                raise APIAuthenticationException(
                                    "OpenAI", f"Authentication error (HTTP {response.status})")

                        # Default error if no specific error was raised
                        raise AIModelException(
                            self.model_name, f"API error: HTTP {response.status}")

        except (AIModelException, APIRateLimitException, APIAuthenticationException):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error generating OpenAI embedding: {str(e)}")
            raise AIModelException(
                self.model_name, f"Unexpected error: {str(e)}")

    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate vector embeddings for a batch of texts.

        Args:
            texts (List[str]): The texts to generate embeddings for

        Returns:
            List[List[float]]: The vector embeddings
        """
        embeddings = []
        for text in texts:
            try:
                embedding = await self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error(
                    f"Error generating embedding for text: {text[:50]}..., {str(e)}")
                # Add a zero vector for failed embeddings
                embeddings.append([0.0] * 768)

        return embeddings

    @staticmethod
    def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate the cosine similarity between two vectors.

        Args:
            vec1 (List[float]): First vector
            vec2 (List[float]): Second vector

        Returns:
            float: Cosine similarity (-1 to 1, higher is more similar)
        """
        if not vec1 or not vec2:
            return 0.0

        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        return dot_product / (norm_a * norm_b)


# Create a singleton instance
embedding_generator = EmbeddingGenerator()
