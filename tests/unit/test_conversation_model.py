"""
Unit tests for the Conversation model
"""

import pytest
from datetime import datetime

from jyra.db.models.conversation import Conversation
from jyra.db.models.user import User
from jyra.db.models.role import Role


@pytest.mark.asyncio
async def test_add_message():
    """Test adding a message to a conversation."""
    # Create test user and role
    user = User(
        user_id=12349,
        username="conv_user",
        first_name="Conv",
        last_name="User",
        language_code="en"
    )
    await user.save()

    role = Role(
        name="Conv Test Role",
        description="A role for testing conversations",
        personality="Helpful",
        speaking_style="Casual",
        knowledge_areas="Testing",
        behaviors="Helpful",
        is_custom=True,
        created_by=12349
    )
    await role.save()

    # Add a message to the conversation
    success = await Conversation.add_message(
        user_id=12349,
        role_id=role.role_id,
        user_message="Hello, this is a test message",
        bot_response="Hi there! This is a test response"
    )

    # Verify the message was added
    assert success is True

    # Get conversation history
    history = await Conversation.get_conversation_history(
        user_id=12349,
        role_id=role.role_id
    )

    # Verify the history contains our message
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello, this is a test message"

    # Clean up
    await User.delete_user(12349)
    await Role.delete_role(role.role_id)


@pytest.mark.asyncio
async def test_get_conversation_history():
    """Test getting conversation history."""
    # Create test user and role
    user = User(
        user_id=12350,
        username="hist_user",
        first_name="Hist",
        last_name="User",
        language_code="en"
    )
    await user.save()

    role = Role(
        name="Hist Test Role",
        description="A role for testing conversation history",
        personality="Helpful",
        speaking_style="Casual",
        knowledge_areas="Testing",
        behaviors="Helpful",
        is_custom=True,
        created_by=12350
    )
    await role.save()

    # Add multiple messages to the conversation
    await Conversation.add_message(
        user_id=12350,
        role_id=role.role_id,
        user_message="Message 1",
        bot_response="Response 1"
    )

    await Conversation.add_message(
        user_id=12350,
        role_id=role.role_id,
        user_message="Message 2",
        bot_response="Response 2"
    )

    await Conversation.add_message(
        user_id=12350,
        role_id=role.role_id,
        user_message="Message 3",
        bot_response="Response 3"
    )

    # Get conversation history
    history = await Conversation.get_conversation_history(
        user_id=12350,
        role_id=role.role_id
    )

    # Verify the history contains our messages in the correct order
    assert len(history) == 6  # 3 user messages + 3 bot responses

    # Check the order (most recent should be last)
    assert history[0]["content"] == "Message 1"
    assert history[1]["content"] == "Response 1"
    assert history[2]["content"] == "Message 2"
    assert history[3]["content"] == "Response 2"
    assert history[4]["content"] == "Message 3"
    assert history[5]["content"] == "Response 3"

    # Test limit parameter
    limited_history = await Conversation.get_conversation_history(
        user_id=12350,
        role_id=role.role_id,
        limit=2  # Only get the last 2 messages (1 exchange)
    )

    assert len(limited_history) == 2
    assert limited_history[0]["content"] == "Message 3"
    assert limited_history[1]["content"] == "Response 3"

    # Clean up
    await User.delete_user(12350)
    await Role.delete_role(role.role_id)


@pytest.mark.asyncio
async def test_clear_conversation_history():
    """Test clearing conversation history."""
    # Create test user and role
    user = User(
        user_id=12351,
        username="clear_user",
        first_name="Clear",
        last_name="User",
        language_code="en"
    )
    await user.save()

    role = Role(
        name="Clear Test Role",
        description="A role for testing clearing conversation history",
        personality="Helpful",
        speaking_style="Casual",
        knowledge_areas="Testing",
        behaviors="Helpful",
        is_custom=True,
        created_by=12351
    )
    await role.save()

    # Add a message to the conversation
    await Conversation.add_message(
        user_id=12351,
        role_id=role.role_id,
        user_message="Test message",
        bot_response="Test response"
    )

    # Verify the message was added
    history = await Conversation.get_conversation_history(
        user_id=12351,
        role_id=role.role_id
    )
    assert len(history) == 2

    # Clear the conversation history
    success = await Conversation.clear_conversation_history(
        user_id=12351,
        role_id=role.role_id
    )

    # Verify the history was cleared
    assert success is True

    # Get the history again
    cleared_history = await Conversation.get_conversation_history(
        user_id=12351,
        role_id=role.role_id
    )

    # Verify the history is empty
    assert len(cleared_history) == 0

    # Clean up
    await User.delete_user(12351)
    await Role.delete_role(role.role_id)
