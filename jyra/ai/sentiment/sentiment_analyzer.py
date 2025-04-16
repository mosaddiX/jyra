"""
Sentiment analysis module for Jyra
"""

import re
from typing import Dict, Any, Tuple, List, Optional
import aiohttp
import json

from jyra.utils.config import GEMINI_API_KEY
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class SentimentAnalyzer:
    """
    Class for analyzing sentiment in user messages.
    """

    def __init__(self):
        """
        Initialize the sentiment analyzer.
        """
        # Emotion categories
        self.emotions = [
            "happiness", "sadness", "anger", "fear",
            "surprise", "disgust", "neutral", "excitement",
            "confusion", "anxiety", "gratitude", "disappointment"
        ]

        # API endpoint for Gemini
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

        logger.info("Initialized sentiment analyzer")

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze the sentiment of a text message.

        Args:
            text (str): The text to analyze

        Returns:
            Dict[str, Any]: Sentiment analysis results
        """
        try:
            # Use Gemini to analyze sentiment
            result = await self._analyze_with_gemini(text)
            logger.info(
                f"Sentiment analysis completed: {result['primary_emotion']} ({result['intensity']})")
            return result
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            # Return neutral sentiment as fallback
            return {
                "primary_emotion": "neutral",
                "intensity": 3,
                "explanation": "Failed to analyze sentiment"
            }

    async def _analyze_with_gemini(self, text: str) -> Dict[str, Any]:
        """
        Use Gemini to analyze sentiment.

        Args:
            text (str): The text to analyze

        Returns:
            Dict[str, Any]: Sentiment analysis results
        """
        # Create the prompt for sentiment analysis
        prompt = f"""
        You are Jyra, an emotionally intelligent AI companion with exceptional emotional perception abilities.

        Analyze the emotional tone of the following message with nuance and depth:

        "{text}"

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

        # Prepare the API request
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 200,
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

                                # Extract JSON from the response
                                try:
                                    # Find JSON in the response
                                    json_match = re.search(
                                        r'\{.*\}', response_text, re.DOTALL)
                                    if json_match:
                                        json_str = json_match.group(0)
                                        sentiment_data = json.loads(json_str)

                                        # Validate and normalize the response
                                        primary_emotion = sentiment_data.get(
                                            "primary_emotion", "neutral").lower()
                                        intensity = int(
                                            sentiment_data.get("intensity", 3))
                                        explanation = sentiment_data.get(
                                            "explanation", "")

                                        # Ensure intensity is in range 1-5
                                        intensity = max(1, min(5, intensity))

                                        return {
                                            "primary_emotion": primary_emotion,
                                            "intensity": intensity,
                                            "explanation": explanation
                                        }
                                except Exception as e:
                                    logger.error(
                                        f"Error parsing sentiment JSON: {str(e)}")

                # Return neutral sentiment as fallback
                return {
                    "primary_emotion": "neutral",
                    "intensity": 3,
                    "explanation": "Could not determine sentiment"
                }

    def get_response_adjustment(self, sentiment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get adjustments for AI response based on detected sentiment.

        Args:
            sentiment (Dict[str, Any]): Sentiment analysis results

        Returns:
            Dict[str, Any]: Response adjustments
        """
        emotion = sentiment["primary_emotion"]
        intensity = sentiment["intensity"]

        # Default adjustments
        adjustments = {
            "temperature": 0.7,
            "tone_guidance": ""
        }

        # Adjust based on emotion and intensity
        if emotion == "happiness" or emotion == "excitement" or emotion == "gratitude":
            # For positive emotions, match the energy level
            adjustments["temperature"] = min(0.8, 0.6 + (intensity * 0.05))
            adjustments["tone_guidance"] = f"The user seems {emotion}. Respond with matching positive energy and enthusiasm."

        elif emotion == "sadness" or emotion == "disappointment":
            # For sad emotions, be more empathetic and supportive
            adjustments["temperature"] = max(0.5, 0.7 - (intensity * 0.05))
            adjustments["tone_guidance"] = f"The user seems {emotion}. Respond with empathy, warmth, and support."

        elif emotion == "anger" or emotion == "disgust":
            # For negative emotions, be calm and de-escalating
            adjustments["temperature"] = max(0.4, 0.7 - (intensity * 0.06))
            adjustments["tone_guidance"] = f"The user seems {emotion}. Respond calmly and with understanding, avoiding escalation."

        elif emotion == "fear" or emotion == "anxiety":
            # For fearful emotions, be reassuring
            adjustments["temperature"] = max(0.5, 0.7 - (intensity * 0.04))
            adjustments["tone_guidance"] = f"The user seems {emotion}. Respond with reassurance and support."

        elif emotion == "confusion":
            # For confusion, be clear and helpful
            adjustments["temperature"] = max(0.5, 0.7 - (intensity * 0.05))
            adjustments["tone_guidance"] = f"The user seems confused. Respond with clarity and helpful guidance."

        elif emotion == "surprise":
            # For surprise, match the energy but provide context
            adjustments["temperature"] = min(0.8, 0.6 + (intensity * 0.04))
            adjustments["tone_guidance"] = f"The user seems surprised. Acknowledge this and provide context or explanation."

        else:  # neutral or unrecognized
            adjustments["tone_guidance"] = "Respond in a balanced, conversational tone."

        return adjustments
