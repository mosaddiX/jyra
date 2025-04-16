"""
Memory extraction module for Jyra.

This module extracts memories from user messages using AI.
"""

import logging
from typing import List, Dict, Any, Optional

from jyra.ai.models.gemini_direct import GeminiAI
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryExtractor:
    """
    Class for extracting memories from user messages using AI.
    """

    def __init__(self):
        """Initialize the memory extractor."""
        self.ai = GeminiAI()

    async def extract_memories(self, user_message: str, user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract memories from a user message.

        Args:
            user_message (str): The user's message
            user_context (Optional[Dict[str, Any]]): Context about the user

        Returns:
            List[Dict[str, Any]]: List of extracted memories with category, importance, and content
        """
        if not user_message or len(user_message.strip()) < 10:
            return []

        try:
            # Create a prompt for the AI to extract memories
            prompt = self._create_memory_extraction_prompt(user_message, user_context)
            
            # Get response from AI
            response = await self.ai.generate_response(prompt)
            
            # Parse the response to extract memories
            memories = self._parse_memory_response(response)
            
            return memories
        
        except Exception as e:
            logger.error(f"Error extracting memories: {str(e)}")
            return []

    def _create_memory_extraction_prompt(self, user_message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a prompt for memory extraction.

        Args:
            user_message (str): The user's message
            user_context (Optional[Dict[str, Any]]): Context about the user

        Returns:
            str: The prompt for the AI
        """
        context_str = ""
        if user_context:
            context_str = "User context:\n"
            for key, value in user_context.items():
                context_str += f"- {key}: {value}\n"

        prompt = f"""
You are an AI assistant that extracts important information from user messages that should be remembered for future conversations.

Extract facts, preferences, personal details, and other important information from the following message. 
Focus on information that would be useful to remember for future conversations.

For each piece of information, provide:
1. The exact content to remember
2. The category (personal, preference, fact, event, relationship, etc.)
3. An importance score (1-5, where 5 is most important)

Format your response as a JSON array of objects with the following structure:
[
  {{
    "content": "The exact information to remember",
    "category": "category_name",
    "importance": importance_score
  }}
]

If there's nothing worth remembering, return an empty array: []

{context_str}
User message: {user_message}

Extracted memories (JSON format):
"""
        return prompt

    def _parse_memory_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the AI response to extract memories.

        Args:
            response (str): The AI's response

        Returns:
            List[Dict[str, Any]]: List of extracted memories
        """
        try:
            # Clean up the response
            response = response.strip()
            
            # If the response is empty or indicates no memories, return empty list
            if not response or response == "[]":
                return []
            
            # Try to extract JSON from the response
            import json
            
            # Find the start and end of the JSON array
            start_idx = response.find("[")
            end_idx = response.rfind("]") + 1
            
            if start_idx == -1 or end_idx == 0:
                logger.warning(f"Could not find JSON array in response: {response}")
                return []
            
            json_str = response[start_idx:end_idx]
            memories = json.loads(json_str)
            
            # Validate the memories
            valid_memories = []
            for memory in memories:
                if "content" in memory and "category" in memory and "importance" in memory:
                    # Ensure importance is an integer between 1 and 5
                    importance = int(memory["importance"])
                    if importance < 1:
                        importance = 1
                    elif importance > 5:
                        importance = 5
                    
                    valid_memories.append({
                        "content": memory["content"],
                        "category": memory["category"],
                        "importance": importance
                    })
            
            return valid_memories
            
        except Exception as e:
            logger.error(f"Error parsing memory response: {str(e)}")
            return []


# Create a singleton instance
memory_extractor = MemoryExtractor()
