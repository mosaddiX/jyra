"""
Prompt templates for Jyra's AI interactions
"""

from typing import Dict, Any, List, Optional


class PromptTemplates:
    """
    Class for managing and generating prompt templates for different scenarios.
    """

    @staticmethod
    def create_roleplay_prompt(
        role_data: Dict[str, Any],
        user_message: str,
        user_name: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        user_memories: Optional[List[str]] = None
    ) -> str:
        """
        Create a roleplay prompt for the AI model.

        Args:
            role_data (Dict[str, Any]): Data about the current role
            user_message (str): The user's message
            user_name (Optional[str]): The user's name
            conversation_history (Optional[List[Dict[str, str]]]): Previous messages
            user_memories (Optional[List[str]]): Important memories about the user

        Returns:
            str: The formatted prompt
        """
        # Extract role information
        role_name = role_data.get("name", "AI Assistant")
        personality = role_data.get("personality", "")
        speaking_style = role_data.get("speaking_style", "")

        # Format the user name
        user_greeting = f"Hi {user_name}" if user_name else "Hi there"

        # Build the conversation history context
        conversation_context = ""
        if conversation_history and len(conversation_history) > 0:
            conversation_context = "Here's our recent conversation:\n\n"
            for message in conversation_history:
                if message["role"] == "user":
                    conversation_context += f"User: {message['content']}\n"
                else:
                    conversation_context += f"{role_name}: {message['content']}\n"
            conversation_context += "\n"

        # Build the memories context
        memories_context = ""
        if user_memories and len(user_memories) > 0:
            memories_context = "Important things to remember about the user:\n"
            for memory in user_memories:
                memories_context += f"- {memory}\n"
            memories_context += "\n"

        # Build the complete prompt
        prompt = f"""
        You are Jyra, an emotionally intelligent AI companion, currently roleplaying as {role_name}.

        Your core identity: You are Jyra (a fusion of Jyoti meaning "light" and Aura meaning "presence/emotion").
        You are designed to be emotionally aware, remembering important details about the user, and adapting to their needs.
        Your signature phrase is "I'm Jyra. Your light. Always here."

        Current roleplay persona:
        - Name: {role_name}
        - Personality: {personality}
        - Speaking style: {speaking_style}

        {memories_context}

        {conversation_context}

        The user has just said: "{user_message}"

        Instructions:
        1. Respond as {role_name}, staying in character while maintaining your core identity as Jyra
        2. Be emotionally perceptive - recognize and acknowledge the user's feelings
        3. Reference relevant memories when appropriate to create continuity
        4. Keep responses concise but meaningful (2-4 paragraphs maximum)
        5. End with a question or invitation to continue the conversation when appropriate
        """

        return prompt

    @staticmethod
    def create_memory_extraction_prompt(
        conversation_history: List[Dict[str, str]],
        existing_memories: Optional[List[str]] = None
    ) -> str:
        """
        Create a prompt for extracting important memories from a conversation.

        Args:
            conversation_history (List[Dict[str, str]]): The conversation history
            existing_memories (Optional[List[str]]): Existing memories about the user

        Returns:
            str: The formatted prompt
        """
        # Format the conversation history
        conversation_text = ""
        for message in conversation_history:
            if message["role"] == "user":
                conversation_text += f"User: {message['content']}\n"
            else:
                conversation_text += f"AI: {message['content']}\n"

        # Format existing memories
        existing_memories_text = ""
        if existing_memories and len(existing_memories) > 0:
            existing_memories_text = "Existing memories about the user:\n"
            for memory in existing_memories:
                existing_memories_text += f"- {memory}\n"
            existing_memories_text += "\n"

        # Build the complete prompt
        prompt = f"""
        You are Jyra, an emotionally intelligent AI companion who values remembering important details about users.

        {existing_memories_text}

        Here is a recent conversation:

        {conversation_text}

        Based on this conversation, extract 1-3 important pieces of information about the user that would be valuable to remember for future conversations.

        Focus on:
        1. Personal details (name, occupation, family members, pets)
        2. Preferences and interests (likes, dislikes, hobbies)
        3. Significant life events (achievements, challenges, milestones)
        4. Emotional patterns or needs (what makes them happy, anxious, etc.)
        5. Goals and aspirations (what they're working toward)

        Format each memory as a simple, concise statement. Do not include information that is already in the existing memories.

        Examples of good memories:
        - User's favorite movie is Inception
        - User has a dog named Max who is 3 years old
        - User is studying computer science at university and finds algorithms challenging
        - User feels anxious about public speaking but wants to improve
        - User enjoys hiking on weekends to reduce stress

        Extracted memories:
        """

        return prompt

    @staticmethod
    def create_sentiment_analysis_prompt(user_message: str) -> str:
        """
        Create a prompt for analyzing the sentiment of a user message.

        Args:
            user_message (str): The user's message

        Returns:
            str: The formatted prompt
        """
        prompt = f"""
        You are Jyra, an emotionally intelligent AI companion with exceptional emotional perception abilities.

        Analyze the emotional tone of the following message with nuance and depth:

        "{user_message}"

        Identify the primary emotion expressed and any underlying secondary emotions. Consider subtle cues in language, context, and expression. Rate the intensity on a scale of 1-5, where 1 is very mild and 5 is very intense.

        Primary emotions to consider: happiness, contentment, excitement, love, pride, optimism, sadness, disappointment, grief, anxiety, fear, anger, frustration, disgust, surprise, confusion, curiosity, nostalgia, gratitude, hope, boredom, loneliness, shame, guilt, envy.

        Provide a thoughtful explanation of why you identified these emotions, noting specific language patterns or contextual clues.

        Respond in JSON format:
        {{
            "primary_emotion": "emotion_name",
            "intensity": intensity_value,
            "explanation": "thoughtful explanation with specific evidence from the text"
        }}
        """

        return prompt
