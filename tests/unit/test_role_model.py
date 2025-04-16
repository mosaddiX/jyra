"""
Unit tests for the Role model
"""

import pytest

from jyra.db.models.role import Role


@pytest.mark.asyncio
async def test_role_creation():
    """Test creating a new role."""
    # Create a test role
    role = Role(
        name="Test Role",
        description="A role for testing",
        personality="Helpful and friendly",
        speaking_style="Casual and conversational",
        knowledge_areas="Testing and quality assurance",
        behaviors="Responds helpfully to test queries",
        is_custom=True,
        created_by=12345
    )

    # Save the role
    success = await role.save()

    # Verify the role was saved
    assert success is True
    assert role.role_id is not None

    # Get the role from the database
    db_role = await Role.get_role(role.role_id)

    # Verify the role was retrieved correctly
    assert db_role is not None
    assert db_role.name == "Test Role"
    assert db_role.description == "A role for testing"
    assert db_role.personality == "Helpful and friendly"
    assert db_role.speaking_style == "Casual and conversational"
    assert db_role.knowledge_areas == "Testing and quality assurance"
    assert db_role.behaviors == "Responds helpfully to test queries"
    assert db_role.is_custom is True
    assert db_role.created_by == 12345

    # Clean up
    await Role.delete_role(role.role_id)


@pytest.mark.asyncio
async def test_get_all_roles():
    """Test getting all roles."""
    # Create test roles
    role1 = Role(
        name="Test Role 1",
        description="First test role",
        personality="Helpful",
        speaking_style="Casual",
        knowledge_areas="Testing",
        behaviors="Helpful",
        is_custom=True,
        created_by=12345
    )

    role2 = Role(
        name="Test Role 2",
        description="Second test role",
        personality="Friendly",
        speaking_style="Formal",
        knowledge_areas="Quality assurance",
        behaviors="Thorough",
        is_custom=True,
        created_by=12345
    )

    # Save the roles
    await role1.save()
    await role2.save()

    # Get all roles
    all_roles = await Role.get_all_roles()

    # Verify roles were retrieved
    assert len(all_roles) >= 2  # There might be default roles

    # Find our test roles in the list
    test_role_1 = next((r for r in all_roles if r.name == "Test Role 1"), None)
    test_role_2 = next((r for r in all_roles if r.name == "Test Role 2"), None)

    assert test_role_1 is not None
    assert test_role_2 is not None

    # Clean up
    await Role.delete_role(role1.role_id)
    await Role.delete_role(role2.role_id)


@pytest.mark.asyncio
async def test_get_custom_roles():
    """Test getting custom roles for a user."""
    # Create test roles
    role1 = Role(
        name="Custom Role 1",
        description="First custom role",
        personality="Helpful",
        speaking_style="Casual",
        knowledge_areas="Testing",
        behaviors="Helpful",
        is_custom=True,
        created_by=12345
    )

    role2 = Role(
        name="Custom Role 2",
        description="Second custom role",
        personality="Friendly",
        speaking_style="Formal",
        knowledge_areas="Quality assurance",
        behaviors="Thorough",
        is_custom=True,
        created_by=12345
    )

    role3 = Role(
        name="Custom Role 3",
        description="Third custom role",
        personality="Analytical",
        speaking_style="Technical",
        knowledge_areas="Programming",
        behaviors="Detailed",
        is_custom=True,
        created_by=54321  # Different user
    )

    # Save the roles
    await role1.save()
    await role2.save()
    await role3.save()

    # Get custom roles for user 12345
    custom_roles = await Role.get_custom_roles(12345)

    # Verify roles were retrieved correctly
    assert len(custom_roles) >= 2

    # Find our test roles in the list
    test_role_1 = next(
        (r for r in custom_roles if r.name == "Custom Role 1"), None)
    test_role_2 = next(
        (r for r in custom_roles if r.name == "Custom Role 2"), None)
    test_role_3 = next(
        (r for r in custom_roles if r.name == "Custom Role 3"), None)

    assert test_role_1 is not None
    assert test_role_2 is not None
    assert test_role_3 is None  # Should not be in the list (different user)

    # Clean up
    await Role.delete_role(role1.role_id)
    await Role.delete_role(role2.role_id)
    await Role.delete_role(role3.role_id)


@pytest.mark.asyncio
async def test_role_to_dict():
    """Test converting a role to a dictionary."""
    # Create a test role
    role = Role(
        name="Dict Test Role",
        description="A role for testing dict conversion",
        personality="Helpful and friendly",
        speaking_style="Casual and conversational",
        knowledge_areas="Testing and quality assurance",
        behaviors="Responds helpfully to test queries",
        is_custom=True,
        created_by=12345
    )

    # Convert to dictionary
    role_dict = role.to_dict()

    # Verify dictionary contents
    assert role_dict["name"] == "Dict Test Role"
    assert role_dict["description"] == "A role for testing dict conversion"
    assert role_dict["personality"] == "Helpful and friendly"
    assert role_dict["speaking_style"] == "Casual and conversational"
    assert role_dict["knowledge_areas"] == "Testing and quality assurance"
    assert role_dict["behaviors"] == "Responds helpfully to test queries"
