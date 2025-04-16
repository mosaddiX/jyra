"""
Google Gemini AI model integration for Jyra using direct API calls
"""

import json
import aiohttp
import os
from typing import List, Dict, Any, Optional

from jyra.utils.config import GEMINI_API_KEY
from jyra.utils.logger import setup_logger
from jyra.ai.cache.response_cache import ResponseCache

logger = setup_logger(__name__)


class GeminiAI:
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
        self.model_name = model_name
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"

        # Initialize cache if enabled
        self.use_cache = use_cache
        if use_cache:
            self.cache = ResponseCache(max_age_seconds=cache_max_age)

        logger.info(f"Initialized Gemini AI with model: {model_name}")

    async def generate_response(
        self,
        prompt: str,
        role_context: Dict[str, Any],
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        bypass_cache: bool = False
    ) -> str:
        """
        Generate a response from the AI model based on the prompt and context.

        Args:
            prompt (str): The user's message
            role_context (Dict[str, Any]): Context about the current role
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            temperature (float): Creativity parameter (0.0 to 1.0)
            max_tokens (int): Maximum response length
            bypass_cache (bool): Whether to bypass the cache

        Returns:
            str: The generated response
        """
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
                    "topP": 0.95,
                    "topK": 40
                }
            }

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

                        logger.error(f"Unexpected response format: {result}")
                        return "I received a response but couldn't understand it. Please try again."
                    else:
                        error_text = await response.text()
                        logger.error(
                            f"API error: {response.status}, {error_text}")
                        return f"I'm having trouble connecting to my AI brain right now (Error {response.status}). Please try again in a moment."

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I'm having trouble connecting to my AI brain right now. Could you try again in a moment?"

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
