"""
AI model manager for Jyra.

This module provides a manager for multiple AI models with fallback capabilities.
"""

from typing import List, Dict, Any, Optional, Union, Tuple
import random

from jyra.ai.models.base_model import BaseAIModel
from jyra.ai.models.gemini_direct import GeminiAI
from jyra.ai.models.openai_model import OpenAIModel
from jyra.utils.exceptions import AIModelException, APIRateLimitException, APIAuthenticationException
from jyra.utils.config import ENABLE_OPENAI
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class ModelManager:
    """
    Manager for multiple AI models with fallback capabilities.
    """

    def __init__(self, primary_model: str = "gemini-2.0-flash", fallback_models: Optional[List[str]] = None, enable_openai: bool = False):
        """
        Initialize the model manager.

        Args:
            primary_model (str): The primary model to use
            fallback_models (Optional[List[str]]): List of fallback models in order of preference
            enable_openai (bool): Whether to enable OpenAI models (disabled by default to avoid costs)
        """
        self.models: Dict[str, BaseAIModel] = {}
        self.primary_model_name = primary_model
        self.enable_openai = enable_openai

        # Set fallback models based on OpenAI availability
        if fallback_models is None:
            if enable_openai:
                self.fallback_model_names = [
                    "gpt-3.5-turbo", "gemini-1.5-flash"]
            else:
                self.fallback_model_names = [
                    "gemini-1.5-flash", "gemini-1.5-pro"]
        else:
            self.fallback_model_names = fallback_models

        # Initialize the primary model
        self._initialize_model(primary_model)

        # Initialize fallback models
        for model_name in self.fallback_model_names:
            self._initialize_model(model_name)

        logger.info(
            f"Initialized model manager with primary model: {primary_model} and fallbacks: {self.fallback_model_names}")

    def _initialize_model(self, model_name: str) -> None:
        """
        Initialize a model by name.

        Args:
            model_name (str): The name of the model to initialize
        """
        if model_name in self.models:
            return

        try:
            # Skip OpenAI models if disabled
            if ("gpt" in model_name.lower() or "openai" in model_name.lower()) and not self.enable_openai:
                logger.info(
                    f"Skipping OpenAI model {model_name} (OpenAI is disabled)")
                return

            if "gemini" in model_name.lower():
                self.models[model_name] = GeminiAI(model_name=model_name)
            elif "gpt" in model_name.lower() or "openai" in model_name.lower():
                self.models[model_name] = OpenAIModel(model_name=model_name)
            else:
                logger.warning(
                    f"Unknown model type: {model_name}, defaulting to Gemini")
                self.models[model_name] = GeminiAI(model_name=model_name)

            logger.info(f"Initialized model: {model_name}")
        except Exception as e:
            logger.error(f"Error initializing model {model_name}: {str(e)}")

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
        use_fallbacks: bool = True,
        **kwargs
    ) -> Tuple[str, str]:
        """
        Generate a response using the primary model with fallback to others if needed.

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
            use_fallbacks (bool): Whether to use fallback models if the primary fails
            **kwargs: Additional model-specific parameters

        Returns:
            Tuple[str, str]: The generated response and the name of the model that generated it
        """
        # Try the primary model first
        model_name = self.primary_model_name
        model = self.models.get(model_name)

        if not model:
            logger.warning(
                f"Primary model {model_name} not initialized, trying to initialize it")
            self._initialize_model(model_name)
            model = self.models.get(model_name)

            if not model:
                logger.error(
                    f"Failed to initialize primary model {model_name}")
                if not use_fallbacks or not self.fallback_model_names:
                    raise AIModelException(
                        model_name, "Failed to initialize model and no fallbacks available")

                # Try to use a fallback model
                model_name = self.fallback_model_names[0]
                model = self.models.get(model_name)

                if not model:
                    logger.error(
                        f"Failed to initialize fallback model {model_name}")
                    raise AIModelException(
                        model_name, "Failed to initialize all models")

        # Try to generate a response with the selected model
        try:
            response = await model.generate_response(
                prompt=prompt,
                role_context=role_context,
                conversation_history=conversation_history,
                memory_context=memory_context,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                top_k=top_k,
                stop_sequences=stop_sequences,
                **kwargs
            )
            return response, model_name
        except (AIModelException, APIRateLimitException, APIAuthenticationException) as e:
            logger.error(f"Error with model {model_name}: {str(e)}")

            # If fallbacks are disabled or no fallbacks are available, re-raise the exception
            if not use_fallbacks or not self.fallback_model_names:
                raise

            # Try fallback models
            for fallback_name in self.fallback_model_names:
                if fallback_name == model_name:
                    continue  # Skip if it's the same as the failed model

                fallback_model = self.models.get(fallback_name)
                if not fallback_model:
                    logger.warning(
                        f"Fallback model {fallback_name} not initialized, trying to initialize it")
                    self._initialize_model(fallback_name)
                    fallback_model = self.models.get(fallback_name)

                if not fallback_model:
                    logger.error(
                        f"Failed to initialize fallback model {fallback_name}")
                    continue

                try:
                    logger.info(f"Trying fallback model: {fallback_name}")
                    response = await fallback_model.generate_response(
                        prompt=prompt,
                        role_context=role_context,
                        conversation_history=conversation_history,
                        memory_context=memory_context,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=top_p,
                        top_k=top_k,
                        stop_sequences=stop_sequences,
                        **kwargs
                    )
                    return response, fallback_name
                except Exception as fallback_error:
                    logger.error(
                        f"Error with fallback model {fallback_name}: {str(fallback_error)}")
                    continue

            # If all models failed, raise the original exception
            raise

    async def get_available_models(self) -> List[str]:
        """
        Get a list of available models.

        Returns:
            List[str]: List of available model names
        """
        available_models = []

        # Check primary model
        if self.primary_model_name in self.models:
            model = self.models[self.primary_model_name]
            if await model.is_available():
                available_models.append(self.primary_model_name)

        # Check fallback models
        for model_name in self.fallback_model_names:
            if model_name in self.models:
                model = self.models[model_name]
                if await model.is_available():
                    available_models.append(model_name)

        return available_models

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get information about a model.

        Args:
            model_name (str): The name of the model

        Returns:
            Dict[str, Any]: Information about the model
        """
        model = self.models.get(model_name)
        if not model:
            return {
                "name": model_name,
                "available": False,
                "provider": "Unknown",
                "max_context_length": 0,
                "supports_streaming": False,
                "cost_per_1k_tokens": 0.0
            }

        return {
            "name": model.model_name,
            "available": True,
            "provider": model.provider,
            "max_context_length": model.max_context_length,
            "supports_streaming": model.supports_streaming,
            "cost_per_1k_tokens": model.cost_per_1k_tokens
        }

    def clear_all_caches(self) -> Dict[str, int]:
        """
        Clear all model caches.

        Returns:
            Dict[str, int]: Number of cache entries cleared for each model
        """
        results = {}
        for model_name, model in self.models.items():
            try:
                cleared = model.clear_cache()
                results[model_name] = cleared
            except Exception as e:
                logger.error(
                    f"Error clearing cache for model {model_name}: {str(e)}")
                results[model_name] = -1

        return results


# Create a singleton instance using the ENABLE_OPENAI config
model_manager = ModelManager(enable_openai=ENABLE_OPENAI)
