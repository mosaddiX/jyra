"""
Integration tests for the Gemini AI model
"""

import pytest
import os

from jyra.ai.models.gemini_direct import GeminiAI

# Skip these tests if no API key is available
pytestmark = pytest.mark.skipif(
    os.environ.get("GEMINI_API_KEY") is None,
    reason="GEMINI_API_KEY environment variable not set"
)


@pytest.mark.asyncio
async def test_generate_response():
    """Test generating a response from the Gemini AI model."""
    # Initialize the model
    model = GeminiAI()

    # Define a simple role context
    role_context = {
        "name": "Test Assistant",
        "personality": "Helpful and friendly",
        "speaking_style": "Casual and conversational",
        "knowledge_areas": "General knowledge",
        "behaviors": "Responds helpfully to questions"
    }

    # Generate a response
    response = await model.generate_response(
        prompt="Hello, how are you today?",
        role_context=role_context
    )

    # Verify a response was generated
    assert response is not None
    assert len(response) > 0

    # The response should be in character
    assert "I'm having trouble" not in response.lower()


@pytest.mark.asyncio
async def test_conversation_context():
    """Test that the model uses conversation context."""
    # Initialize the model
    model = GeminiAI()

    # Define a simple role context
    role_context = {
        "name": "Test Assistant",
        "personality": "Helpful and friendly",
        "speaking_style": "Casual and conversational",
        "knowledge_areas": "General knowledge",
        "behaviors": "Responds helpfully to questions"
    }

    # Create a conversation history
    conversation_history = [
        {"role": "user", "content": "My name is John."},
        {"role": "assistant", "content": "Nice to meet you, John! How can I help you today?"}
    ]

    # Generate a response that should reference the name
    response = await model.generate_response(
        prompt="What's my name?",
        role_context=role_context,
        conversation_history=conversation_history
    )

    # Verify the response references the name from the conversation history
    assert "John" in response


@pytest.mark.asyncio
async def test_role_context_influence():
    """Test that the role context influences the response."""
    # Initialize the model
    model = GeminiAI()

    # Define a pirate role context
    pirate_context = {
        "name": "Captain Blackbeard",
        "personality": "Gruff, adventurous, and bold",
        "speaking_style": "Pirate slang with lots of 'arr' and 'matey'",
        "knowledge_areas": "Sailing, treasure hunting, naval warfare",
        "behaviors": "Speaks like a pirate, tells tales of the sea"
    }

    # Generate a response with the pirate context
    pirate_response = await model.generate_response(
        prompt="Tell me about yourself.",
        role_context=pirate_context
    )

    # Define a scientist role context
    scientist_context = {
        "name": "Dr. Einstein",
        "personality": "Analytical, curious, and precise",
        "speaking_style": "Academic and thoughtful",
        "knowledge_areas": "Physics, mathematics, scientific research",
        "behaviors": "Explains complex concepts clearly, references scientific principles"
    }

    # Generate a response with the scientist context
    scientist_response = await model.generate_response(
        prompt="Tell me about yourself.",
        role_context=scientist_context
    )

    # Verify the responses are different and reflect their respective contexts
    assert pirate_response != scientist_response

    # The pirate response should contain pirate-like language
    pirate_terms = ["arr", "matey", "sea", "ship", "captain", "sail"]
    has_pirate_term = any(term in pirate_response.lower()
                          for term in pirate_terms)
    assert has_pirate_term

    # The scientist response should contain scientific language
    science_terms = ["research", "science",
                     "physics", "theory", "study", "discover"]
    has_science_term = any(term in scientist_response.lower()
                           for term in science_terms)
    assert has_science_term
