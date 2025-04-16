"""
Unit tests for the Memory model
"""

import pytest
from datetime import datetime

from jyra.db.models.memory import Memory
from jyra.db.models.user import User


@pytest.mark.asyncio
async def test_add_memory():
    """Test adding a memory."""
    # Create test user
    user = User(
        user_id=12352,
        username="mem_user",
        first_name="Mem",
        last_name="User",
        language_code="en"
    )
    await user.save()

    # Add a memory
    memory = Memory(
        user_id=12352,
        content="This is a test memory"
    )

    # Save the memory
    success = await memory.save()

    # Verify the memory was saved
    assert success is True
    assert memory.memory_id is not None

    # Get the memory from the database
    memories = await Memory.get_memories(12352)

    # Verify the memory was retrieved correctly
    assert len(memories) == 1
    assert memories[0].user_id == 12352
    assert memories[0].content == "This is a test memory"

    # Clean up
    await Memory.delete_memory(memory.memory_id)
    await User.delete_user(12352)


@pytest.mark.asyncio
async def test_get_memories():
    """Test getting memories for a user."""
    # Create test user
    user = User(
        user_id=12353,
        username="mems_user",
        first_name="Mems",
        last_name="User",
        language_code="en"
    )
    await user.save()

    # Add multiple memories
    memory1 = Memory(
        user_id=12353,
        content="Memory 1"
    )
    await memory1.save()

    memory2 = Memory(
        user_id=12353,
        content="Memory 2"
    )
    await memory2.save()

    memory3 = Memory(
        user_id=12353,
        content="Memory 3"
    )
    await memory3.save()

    # Get all memories
    all_memories = await Memory.get_memories(12353)

    # Verify all memories were retrieved
    assert len(all_memories) == 3

    # Test limit parameter
    limited_memories = await Memory.get_memories(12353, limit=2)

    # Verify limit works
    assert len(limited_memories) == 2

    # Clean up
    await Memory.delete_memory(memory1.memory_id)
    await Memory.delete_memory(memory2.memory_id)
    await Memory.delete_memory(memory3.memory_id)
    await User.delete_user(12353)


@pytest.mark.asyncio
async def test_delete_memory():
    """Test deleting a memory."""
    # Create test user
    user = User(
        user_id=12354,
        username="del_user",
        first_name="Del",
        last_name="User",
        language_code="en"
    )
    await user.save()

    # Add a memory
    memory = Memory(
        user_id=12354,
        content="Memory to delete"
    )
    await memory.save()

    # Verify the memory was added
    memories_before = await Memory.get_memories(12354)
    assert len(memories_before) == 1

    # Delete the memory
    success = await Memory.delete_memory(memory.memory_id)

    # Verify the deletion was successful
    assert success is True

    # Verify the memory was deleted
    memories_after = await Memory.get_memories(12354)
    assert len(memories_after) == 0

    # Clean up
    await User.delete_user(12354)


@pytest.mark.asyncio
async def test_search_memories():
    """Test searching memories."""
    # Create test user
    user = User(
        user_id=12355,
        username="search_user",
        first_name="Search",
        last_name="User",
        language_code="en"
    )
    await user.save()

    # Add memories with different content
    memory1 = Memory(
        user_id=12355,
        content="I like apples and oranges"
    )
    await memory1.save()

    memory2 = Memory(
        user_id=12355,
        content="Bananas are my favorite fruit"
    )
    await memory2.save()

    memory3 = Memory(
        user_id=12355,
        content="I don't like vegetables"
    )
    await memory3.save()

    # Search for memories containing "fruit"
    fruit_memories = await Memory.search_memories(12355, "fruit")

    # Verify search results
    assert len(fruit_memories) == 1
    assert fruit_memories[0].content == "Bananas are my favorite fruit"

    # Search for memories containing "like"
    like_memories = await Memory.search_memories(12355, "like")

    # Verify search results
    assert len(like_memories) == 2

    # Clean up
    await Memory.delete_memory(memory1.memory_id)
    await Memory.delete_memory(memory2.memory_id)
    await Memory.delete_memory(memory3.memory_id)
    await User.delete_user(12355)
