"""
Memory extraction module for Jyra.

This module extracts memories from user messages using AI.
"""

from typing import List, Dict, Any, Optional, Tuple

from jyra.ai.models.model_manager import model_manager
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryExtractor:
    """
    Class for extracting memories from user messages using AI.
    """

    def __init__(self):
        """Initialize the memory extractor."""
        # We'll use the model_manager instead of a specific AI model

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
            prompt = self._create_memory_extraction_prompt(
                user_message, user_context)

            # Get response from AI
            # Create a simple role context for memory extraction
            memory_role_context = {
                "name": "Memory Extractor",
                "personality": "Analytical and precise",
                "speaking_style": "Concise and structured",
                "knowledge_areas": "Personal information extraction, categorization",
                "behaviors": "Identifies important information, categorizes effectively"
            }

            # Use model_manager with fallback capability
            response_tuple = await model_manager.generate_response(
                prompt=prompt,
                role_context=memory_role_context,
                temperature=0.3,  # Lower temperature for more consistent extraction
                max_tokens=500,   # Limit response length
                use_fallbacks=True
            )

            # Extract response and model used
            response, model_used = response_tuple
            logger.info(f"Memory extraction using model: {model_used}")

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
2. The category (personal, preference, fact, event, relationship, opinion, goal, etc.)
3. An importance score (1-5, where 5 is most important)
4. A confidence score (0.1-1.0, where 1.0 is completely certain)
5. A list of relevant tags (2-5 tags that help categorize this memory)
6. An expiration date (ISO format YYYY-MM-DD) if the information is temporary, or null if permanent

Format your response as a JSON array of objects with the following structure:
[
  {{
    "content": "The exact information to remember",
    "category": "category_name",
    "importance": importance_score,
    "confidence": confidence_score,
    "tags": ["tag1", "tag2", "tag3"],
    "expires_at": "YYYY-MM-DD" or null
  }}
]

If there's nothing worth remembering, return an empty array: []

Guidelines for extraction:
- Extract specific, actionable information rather than vague statements
- Assign higher importance to personal preferences, strong opinions, and life events
- Assign lower confidence to inferred information vs. explicitly stated facts
- Use tags that would help retrieve this memory in relevant contexts
- Set expiration dates for time-sensitive information (e.g., upcoming events)

{context_str}
User message: {user_message}

Extracted memories (JSON format):
"""
        return prompt

    def _parse_memory_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse the AI response to extract memories with enhanced fields.

        Args:
            response (str): The AI's response

        Returns:
            List[Dict[str, Any]]: List of extracted memories with enhanced fields
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
                logger.warning(
                    f"Could not find JSON array in response: {response}")
                return []

            json_str = response[start_idx:end_idx]
            memories = json.loads(json_str)

            # Validate the memories with enhanced fields
            valid_memories = []
            for memory in memories:
                if "content" in memory and "category" in memory and "importance" in memory:
                    # Ensure importance is an integer between 1 and 5
                    importance = int(memory["importance"])
                    if importance < 1:
                        importance = 1
                    elif importance > 5:
                        importance = 5

                    # Ensure confidence is a float between 0.1 and 1.0
                    confidence = float(memory.get("confidence", 0.8))
                    if confidence < 0.1:
                        confidence = 0.1
                    elif confidence > 1.0:
                        confidence = 1.0

                    # Process tags
                    tags = memory.get("tags", [])
                    if not isinstance(tags, list):
                        tags = []

                    # Validate tags
                    valid_tags = []
                    for tag in tags:
                        if isinstance(tag, str) and tag.strip():
                            valid_tags.append(tag.strip().lower())

                    # Limit to 5 tags maximum
                    valid_tags = valid_tags[:5]

                    # Process expiration date
                    expires_at = memory.get("expires_at")
                    if expires_at and expires_at.lower() == "null":
                        expires_at = None

                    # Validate expiration date format (YYYY-MM-DD)
                    if expires_at and isinstance(expires_at, str):
                        try:
                            # Simple validation - could be enhanced with datetime parsing
                            if not (len(expires_at) == 10 and expires_at[4] == '-' and expires_at[7] == '-'):
                                expires_at = None
                        except:
                            expires_at = None

                    valid_memories.append({
                        "content": memory["content"],
                        "category": memory["category"],
                        "importance": importance,
                        "confidence": confidence,
                        "tags": valid_tags,
                        "expires_at": expires_at
                    })

            return valid_memories

        except Exception as e:
            logger.error(f"Error parsing memory response: {str(e)}")
            return []


# Create a singleton instance
memory_extractor = MemoryExtractor()
