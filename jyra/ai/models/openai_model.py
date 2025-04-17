"""
OpenAI model implementation for Jyra.
"""

import json
import aiohttp
from typing import List, Dict, Any, Optional

from jyra.ai.models.base_model import BaseAIModel
from jyra.utils.config import OPENAI_API_KEY
from jyra.utils.exceptions import AIModelException, APIRateLimitException, APIAuthenticationException
from jyra.utils.logger import setup_logger
from jyra.ai.cache.response_cache import ResponseCache

logger = setup_logger(__name__)


class OpenAIModel(BaseAIModel):
    """
    Class for interacting with OpenAI's models.
    """

    def __init__(self, model_name: str = "gpt-3.5-turbo", use_cache: bool = True, cache_max_age: int = 3600):
        """
        Initialize the OpenAI model client.

        Args:
            model_name (str): The name of the OpenAI model to use
            use_cache (bool): Whether to use response caching
            cache_max_age (int): Maximum age of cache entries in seconds
        """
        self._model_name = model_name
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.api_key = OPENAI_API_KEY

        # Initialize cache if enabled
        self.use_cache = use_cache
        if use_cache:
            self.cache = ResponseCache(max_age_seconds=cache_max_age)

        # Model-specific parameters
        if "gpt-4" in model_name:
            self._max_context_length = 128000 if "128k" in model_name else 8192
            self._cost_per_1k_tokens = 0.03  # Input cost, output is higher
        else:  # GPT-3.5
            self._max_context_length = 16384
            self._cost_per_1k_tokens = 0.0015  # Input cost, output is higher
            
        self._supports_streaming = True

        logger.info(f"Initialized OpenAI model: {model_name}")

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
        Generate a response from the OpenAI model.

        Args:
            prompt (str): The user's message
            role_context (Optional[Dict[str, Any]]): Context about the current role
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            memory_context (Optional[str]): Context from user memories
            temperature (float): Creativity parameter (0.0 to 1.0)
            max_tokens (int): Maximum response length
            top_p (float): Nucleus sampling parameter
            top_k (int): Top-k sampling parameter (not used by OpenAI)
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
            # Prepare the messages array for the API request
            messages = []

            # Add system message with role context
            system_prompt = self._build_system_prompt(role_context)
            messages.append({
                "role": "system",
                "content": system_prompt
            })

            # Add memory context if provided
            if memory_context and memory_context.strip():
                memory_prompt = f"Important context about the user:\n{memory_context}"
                messages.append({
                    "role": "system",
                    "content": memory_prompt
                })

            # Add conversation history
            if conversation_history:
                for message in conversation_history:
                    role = "user" if message["role"] == "user" else "assistant"
                    messages.append({
                        "role": role,
                        "content": message["content"]
                    })

            # Add the current user message
            messages.append({
                "role": "user",
                "content": prompt
            })

            # Prepare the request payload
            payload = {
                "model": self._model_name,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": top_p
            }
            
            # Add stop sequences if provided
            if stop_sequences:
                payload["stop"] = stop_sequences

            # Add frequency and presence penalties if provided
            if "frequency_penalty" in kwargs:
                payload["frequency_penalty"] = kwargs["frequency_penalty"]
            if "presence_penalty" in kwargs:
                payload["presence_penalty"] = kwargs["presence_penalty"]

            # Make the API request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"API response status: {response.status}")

                        # Extract the response text
                        if "choices" in result and len(result["choices"]) > 0:
                            choice = result["choices"][0]
                            if "message" in choice and "content" in choice["message"]:
                                response_text = choice["message"]["content"]
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
                            error_message = error_data.get("error", {}).get("message", "Unknown error")
                            error_type = error_data.get("error", {}).get("type", "")
                            
                            # Handle specific error types
                            if response.status == 429 or "rate_limit" in error_type:
                                raise APIRateLimitException("OpenAI", error_message)
                            elif response.status in (401, 403) or "authentication" in error_type:
                                raise APIAuthenticationException("OpenAI", error_message)
                            else:
                                raise AIModelException(self._model_name, f"API error: {error_message}")
                        except json.JSONDecodeError:
                            # If we can't parse the error as JSON, use the status code
                            if response.status == 429:
                                raise APIRateLimitException("OpenAI", f"Rate limit exceeded (HTTP {response.status})")
                            elif response.status in (401, 403):
                                raise APIAuthenticationException("OpenAI", f"Authentication error (HTTP {response.status})")
                            
                        # Default error if no specific error was raised
                        raise AIModelException(self._model_name, f"API error: HTTP {response.status}")

        except (AIModelException, APIRateLimitException, APIAuthenticationException):
            # Re-raise specific exceptions
            raise
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise AIModelException(self._model_name, f"Unexpected error: {str(e)}")

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
        knowledge_areas = role_context.get("knowledge_areas", "General knowledge")
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
                test_url = "https://api.openai.com/v1/models"
                headers = {"Authorization": f"Bearer {self.api_key}"}
                async with session.get(test_url, headers=headers) as response:
                    if response.status == 200:
                        # Check if our model is in the list of available models
                        result = await response.json()
                        if "data" in result:
                            for model in result["data"]:
                                if model.get("id") == self._model_name:
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
        return "OpenAI"

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
