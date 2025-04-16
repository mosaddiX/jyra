"""
Integration tests for the sentiment analyzer
"""

import pytest
import os

from jyra.ai.sentiment.sentiment_analyzer import SentimentAnalyzer

# Skip these tests if no API key is available
pytestmark = pytest.mark.skipif(
    os.environ.get("GEMINI_API_KEY") is None,
    reason="GEMINI_API_KEY environment variable not set"
)


@pytest.mark.asyncio
async def test_analyze_sentiment():
    """Test analyzing sentiment of text."""
    # Initialize the sentiment analyzer
    analyzer = SentimentAnalyzer()

    # Test positive sentiment
    positive_result = await analyzer.analyze_sentiment(
        "I'm so happy today! Everything is going great!"
    )

    # Verify the result
    assert positive_result is not None
    assert "primary_emotion" in positive_result
    assert "intensity" in positive_result
    assert "explanation" in positive_result

    # The primary emotion should be positive
    positive_emotions = ["happiness", "excitement", "gratitude", "joy"]
    assert any(emotion in positive_result["primary_emotion"].lower(
    ) for emotion in positive_emotions)

    # The intensity should be high
    assert positive_result["intensity"] >= 3

    # Test negative sentiment
    negative_result = await analyzer.analyze_sentiment(
        "I'm feeling really sad and disappointed today."
    )

    # Verify the result
    assert negative_result is not None
    assert "primary_emotion" in negative_result

    # The primary emotion should be negative
    negative_emotions = ["sadness", "disappointment", "anger", "fear"]
    assert any(emotion in negative_result["primary_emotion"].lower(
    ) for emotion in negative_emotions)

    # Test neutral sentiment
    neutral_result = await analyzer.analyze_sentiment(
        "The weather today is partly cloudy with a temperature of 72 degrees."
    )

    # Verify the result
    assert neutral_result is not None
    assert "primary_emotion" in neutral_result

    # The primary emotion should be neutral or have low intensity
    assert neutral_result["primary_emotion"].lower(
    ) == "neutral" or neutral_result["intensity"] <= 2


@pytest.mark.asyncio
async def test_get_response_adjustment():
    """Test getting response adjustments based on sentiment."""
    # Initialize the sentiment analyzer
    analyzer = SentimentAnalyzer()

    # Test adjustments for different emotions
    emotions = [
        {"primary_emotion": "happiness", "intensity": 4,
            "explanation": "User is happy"},
        {"primary_emotion": "sadness", "intensity": 3, "explanation": "User is sad"},
        {"primary_emotion": "anger", "intensity": 4, "explanation": "User is angry"},
        {"primary_emotion": "fear", "intensity": 3,
            "explanation": "User is afraid"},
        {"primary_emotion": "neutral", "intensity": 2,
            "explanation": "User is neutral"}
    ]

    for emotion in emotions:
        # Get adjustments
        adjustments = analyzer.get_response_adjustment(emotion)

        # Verify adjustments
        assert adjustments is not None
        assert "temperature" in adjustments
        assert "tone_guidance" in adjustments

        # Verify temperature is within valid range
        assert 0.0 <= adjustments["temperature"] <= 1.0

        # Verify tone guidance contains the emotion
        assert emotion["primary_emotion"] in adjustments["tone_guidance"].lower()

    # Verify that different emotions result in different adjustments
    happy_adjustments = analyzer.get_response_adjustment(emotions[0])
    sad_adjustments = analyzer.get_response_adjustment(emotions[1])

    assert happy_adjustments["temperature"] != sad_adjustments["temperature"]
    assert happy_adjustments["tone_guidance"] != sad_adjustments["tone_guidance"]
