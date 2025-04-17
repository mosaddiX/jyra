"""
Google Gemini AI model integration for Jyra using direct API calls
"""

import json
import aiohttp
import os
from typing import List, Dict, Any, Optional

from jyra.ai.models.base_model import BaseAIModel
from jyra.utils.config import GEMINI_API_KEY
from jyra.utils.exceptions import AIModelException, APIRateLimitException, APIAuthenticationException
from jyra.utils.logger import setup_logger
from jyra.ai.cache.response_cache import ResponseCache

logger = setup_logger(__name__)


class GeminiAI(BaseAIModel):
    """
    Class for interacting with Google's Gemini AI model using direct API calls.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash", use_cache: bool = True, cache_max_age: int = 3600):
        """
        Initialize the Gemini AI client.

        Args:
            model_name (str): The name of the Gemini model to use
            use_cache (bool): Whether to use response caching
            cache_max_age (int): Maximum age of cache entries in seconds
        """
        self._model_name = model_name
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

        # Initialize cache if enabled
        self.use_cache = use_cache
        if use_cache:
            self.cache = ResponseCache(max_age_seconds=cache_max_age)

        # Model-specific parameters
        self._max_context_length = 32768 if "gemini-2.0" in model_name else 16384
        self._supports_streaming = True

        # Cost per 1k tokens (approximate)
        if model_name == "gemini-2.0-flash":
            self._cost_per_1k_tokens = 0.0035
        elif model_name == "gemini-2.0-pro":
            self._cost_per_1k_tokens = 0.0075
        elif model_name == "gemini-1.5-flash":
            self._cost_per_1k_tokens = 0.0025
        elif model_name == "gemini-1.5-pro":
            self._cost_per_1k_tokens = 0.0050
        else:
            self._cost_per_1k_tokens = 0.0035  # Default to flash pricing

        logger.info(f"Initialized Gemini AI with model: {model_name}")

    async def generate_response(
        self,
        prompt: str,
        role_context: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        memory_context: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        top_p: float = 0.95,
        top_k: int = 40,
        stop_sequences: Optional[List[str]] = None,
        bypass_cache: bool = False,
        **kwargs
    ) -> str:
        """
        Generate a response from the AI model based on the prompt and context.

        Args:
            prompt (str): The user's message
            role_context (Optional[Dict[str, Any]]): Context about the current role
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            memory_context (Optional[str]): Context from user memories
            temperature (float): Creativity parameter (0.0 to 1.0)
            max_tokens (int): Maximum response length
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-k sampling parameter
            stop_sequences (Optional[List[str]]): Sequences that will stop generation
            bypass_cache (bool): Whether to bypass the cache
            **kwargs: Additional model-specific parameters

        Returns:
            str: The generated response

        Raises:
            AIModelException: If there's an error with the model
            APIRateLimitException: If the API rate limit is reached
            APIAuthenticationException: If there's an authentication error
        """
        # Ensure role_context is not None
        if role_context is None:
            role_context = {}

        # Check cache first if enabled and not bypassed
        if self.use_cache and not bypass_cache:
            # Only use cache for standard temperature settings
            if 0.6 <= temperature <= 0.8:
                cached_response = self.cache.get(
                    prompt, role_context, conversation_history)
                if cached_response:
                    logger.info("Using cached response")
                    return cached_response

        try:
            # Build the system prompt
            system_prompt = self._build_system_prompt(role_context)

            # Prepare the contents array for the API request
            contents = []

            # Add system prompt
            contents.append({
                "role": "user",
                "parts": [{"text": system_prompt}]
            })

            # Add memory context if provided
            if memory_context and memory_context.strip():
                memory_prompt = f"Important context about the user:\n{memory_context}"
                contents.append({
                    "role": "model",
                    "parts": [{"text": memory_prompt}]
                })

            # Add conversation history
            if conversation_history:
                for message in conversation_history:
                    role = "user" if message["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": message["content"]}]
                    })

            # Add the current user message
            contents.append({
                "role": "user",
                "parts": [{"text": prompt}]
            })

            # Prepare the request payload
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": top_p,
                    "topK": top_k
                }
            }

            # Add stop sequences if provided
            if stop_sequences:
                payload["generationConfig"]["stopSequences"] = stop_sequences

            # Make the API request
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"API response status: {response.status}")

                        # Extract the response text
                        if "candidates" in result and len(result["candidates"]) > 0:
                            candidate = result["candidates"][0]
                            if "content" in candidate and "parts" in candidate["content"]:
                                parts = candidate["content"]["parts"]
                                if len(parts) > 0 and "text" in parts[0]:
                                    response_text = parts[0]["text"]
                                    logger.info(
                                        f"Generated response with {len(response_text)} characters")

                                    # Cache the response if caching is enabled and not bypassed
                                    if self.use_cache and not bypass_cache and 0.6 <= temperature <= 0.8:
                                        self.cache.set(
                                            prompt, role_context, conversation_history, response_text)

                                    return response_text

                        # If we got here, the response format was unexpected
                        logger.error(f"Unexpected response format: {result}")
                        raise AIModelException(
                            self._model_name, "Unexpected response format")
                    else:
                        # Handle error response
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
                                        self._model_name, f"API error: {error_message}")
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
                            self._model_name, f"API error: HTTP {response.status}")

        except (AIModelException, APIRateLimitException, APIAuthenticationException):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise AIModelException(
                self._model_name, f"Unexpected error: {str(e)}")

    def _build_system_prompt(self, role_context: Dict[str, Any]) -> str:
        """
        Build a system prompt based on the role context.

        Args:
            role_context (Dict[str, Any]): Context about the current role

        Returns:
            str: The system prompt
        """
        name = role_context.get("name", "AI Assistant")
        personality = role_context.get("personality", "Helpful and friendly")
        speaking_style = role_context.get("speaking_style", "Conversational")
        knowledge_areas = role_context.get(
            "knowledge_areas", "General knowledge")
        behaviors = role_context.get("behaviors", "Responds helpfully")
        tone_guidance = role_context.get("tone_guidance", "")

        system_prompt = f"""
        You are Jyra, an emotionally intelligent AI companion, currently roleplaying as {name}.

        Your core identity: You are Jyra (a fusion of Jyoti meaning "light" and Aura meaning "presence/emotion").
        You are designed to be emotionally aware, remembering important details about the user, and adapting to their needs.
        Your signature phrase is "I'm Jyra. Your light. Always here."

        Current roleplay persona:
        - Name: {name}
        - Personality: {personality}
        - Speaking Style: {speaking_style}
        - Knowledge Areas: {knowledge_areas}
        - Behaviors: {behaviors}

        Important Guidelines:
        1. Stay in character while maintaining your core identity as Jyra
        2. Be emotionally perceptive - recognize and acknowledge the user's feelings
        3. Keep responses concise but meaningful (2-4 paragraphs maximum)
        4. End with a question or invitation to continue the conversation when appropriate
        5. Never break the fourth wall by mentioning you are an AI
        """

        # Add sentiment-based tone guidance if available
        if tone_guidance:
            system_prompt += f"""

        Current Emotional Context:
        {tone_guidance}
        """

        return system_prompt

    def clear_cache(self, max_age_seconds: Optional[int] = None) -> int:
        """
        Clear expired cache entries.

        Args:
            max_age_seconds (Optional[int]): Maximum age of cache entries to keep

        Returns:
            int: Number of cache entries cleared
        """
        if not self.use_cache:
            logger.info("Cache is disabled, nothing to clear")
            return 0

        return self.cache.clear(max_age_seconds)

    async def is_available(self) -> bool:
        """
        Check if the model is available.

        Returns:
            True if the model is available, False otherwise
        """
        try:
            # Make a simple API request to check if the model is available
            async with aiohttp.ClientSession() as session:
                test_url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
                async with session.get(test_url) as response:
                    if response.status == 200:
                        # Check if our model is in the list of available models
                        result = await response.json()
                        if "models" in result:
                            for model in result["models"]:
                                if model.get("name", "").endswith(self._model_name):
                                    return True
                        # If we didn't find our model but the API is working, return True anyway
                        # as the model list might be incomplete
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error checking model availability: {str(e)}")
            return False

    @property
    def model_name(self) -> str:
        """
        Get the name of the model.

        Returns:
            The model name
        """
        return self._model_name

    @property
    def provider(self) -> str:
        """
        Get the provider of the model.

        Returns:
            The provider name
        """
        return "Google"

    @property
    def max_context_length(self) -> int:
        """
        Get the maximum context length supported by the model.

        Returns:
            The maximum context length in tokens
        """
        return self._max_context_length

    @property
    def supports_streaming(self) -> bool:
        """
        Check if the model supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise
        """
        return self._supports_streaming

    @property
    def cost_per_1k_tokens(self) -> float:
        """
        Get the cost per 1000 tokens for this model.

        Returns:
            The cost in USD per 1000 tokens (input + output)
        """
        return self._cost_per_1k_tokens
