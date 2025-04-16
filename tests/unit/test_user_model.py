"""
Unit tests for the User model
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from jyra.db.models.user import User


@pytest.mark.asyncio
async def test_user_creation():
    """Test creating a new user."""
    # Create a test user
    user = User(
        user_id=12345,
        username="test_user",
        first_name="Test",
        last_name="User",
        language_code="en"
    )

    # Save the user
    success = await user.save()

    # Verify the user was saved
    assert success is True
    assert user.user_id == 12345

    # Get the user from the database
    db_user = await User.get_user(12345)

    # Verify the user was retrieved correctly
    assert db_user is not None
    assert db_user.user_id == 12345
    assert db_user.username == "test_user"
    assert db_user.first_name == "Test"
    assert db_user.last_name == "User"
    assert db_user.language_code == "en"

    # Clean up
    await User.delete_user(12345)


@pytest.mark.asyncio
async def test_user_update():
    """Test updating a user."""
    # Create a test user
    user = User(
        user_id=12346,
        username="test_user2",
        first_name="Test2",
        last_name="User2",
        language_code="fr"
    )

    # Save the user
    await user.save()

    # Update the user
    user.username = "updated_user"
    user.first_name = "Updated"
    success = await user.update()

    # Verify the update was successful
    assert success is True

    # Get the updated user from the database
    db_user = await User.get_user(12346)

    # Verify the user was updated correctly
    assert db_user is not None
    assert db_user.username == "updated_user"
    assert db_user.first_name == "Updated"
    assert db_user.last_name == "User2"

    # Clean up
    await User.delete_user(12346)


@pytest.mark.asyncio
async def test_user_preferences():
    """Test user preferences."""
    # Create a test user
    user = User(
        user_id=12347,
        username="pref_user",
        first_name="Pref",
        last_name="User",
        language_code="en"
    )

    # Save the user
    await user.save()

    # Get default preferences
    prefs = await User.get_user_preferences(12347)

    # Verify default preferences
    assert prefs["language"] == "en"
    assert prefs["response_length"] == "medium"
    assert prefs["formality_level"] == "casual"
    assert prefs["memory_enabled"] is True
    assert prefs["voice_responses_enabled"] is False

    # Update preferences
    new_prefs = {
        "language": "es",
        "response_length": "short",
        "formality_level": "formal"
    }
    success = await User.update_user_preferences(12347, new_prefs)

    # Verify update was successful
    assert success is True

    # Get updated preferences
    updated_prefs = await User.get_user_preferences(12347)

    # Verify preferences were updated correctly
    assert updated_prefs["language"] == "es"
    assert updated_prefs["response_length"] == "short"
    assert updated_prefs["formality_level"] == "formal"
    assert updated_prefs["memory_enabled"] is True  # Unchanged

    # Clean up
    await User.delete_user(12347)


@pytest.mark.asyncio
async def test_last_interaction():
    """Test updating last interaction time."""
    # Create a test user
    user = User(
        user_id=12348,
        username="time_user",
        first_name="Time",
        last_name="User",
        language_code="en"
    )

    # Save the user
    await user.save()

    # Get the user
    db_user = await User.get_user(12348)
    original_time = db_user.last_interaction

    # Wait a moment
    await asyncio.sleep(1)

    # Update last interaction time
    await db_user.update_last_interaction()

    # Get the user again
    updated_user = await User.get_user(12348)
    updated_time = updated_user.last_interaction

    # Verify the time was updated
    assert updated_time > original_time

    # Clean up
    await User.delete_user(12348)
