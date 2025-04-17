"""
Base AI model interface for Jyra.

This module defines the base interface for all AI models used by Jyra.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union


class BaseAIModel(ABC):
    """
    Abstract base class for AI models.
    
    All AI model implementations should inherit from this class
    and implement its abstract methods.
    """
    
    @abstractmethod
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
        **kwargs
    ) -> str:
        """
        Generate a response from the AI model.
        
        Args:
            prompt: The prompt to send to the model
            role_context: Context about the current role
            conversation_history: Previous messages in the conversation
            memory_context: Context from user memories
            temperature: Sampling temperature (higher = more creative)
            max_tokens: Maximum number of tokens to generate
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop_sequences: Sequences that will stop generation
            **kwargs: Additional model-specific parameters
            
        Returns:
            The generated response
        """
        pass
    
    @abstractmethod
    async def is_available(self) -> bool:
        """
        Check if the model is available.
        
        Returns:
            True if the model is available, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Get the name of the model.
        
        Returns:
            The model name
        """
        pass
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """
        Get the provider of the model.
        
        Returns:
            The provider name
        """
        pass
    
    @property
    @abstractmethod
    def max_context_length(self) -> int:
        """
        Get the maximum context length supported by the model.
        
        Returns:
            The maximum context length in tokens
        """
        pass
    
    @property
    @abstractmethod
    def supports_streaming(self) -> bool:
        """
        Check if the model supports streaming responses.
        
        Returns:
            True if streaming is supported, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def cost_per_1k_tokens(self) -> float:
        """
        Get the cost per 1000 tokens for this model.
        
        Returns:
            The cost in USD per 1000 tokens (input + output)
        """
        pass
