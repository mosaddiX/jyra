"""
User model for Jyra
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Union

from jyra.db.connection import execute_query_async
from jyra.utils.exceptions import DatabaseException
from jyra.utils.error_handler import handle_exceptions
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class User:
    """
    Class for managing user data in the database.
    """

    def __init__(self, user_id: int, username: Optional[str] = None,
                 first_name: Optional[str] = None, last_name: Optional[str] = None,
                 language_code: Optional[str] = None):
        """
        Initialize a User object.

        Args:
            user_id (int): Telegram user ID
            username (Optional[str]): Telegram username
            first_name (Optional[str]): User's first name
            last_name (Optional[str]): User's last name
            language_code (Optional[str]): User's language code
        """
        self.user_id = user_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.language_code = language_code
        self.current_role_id = None
        self.is_admin = False
        self.created_at = None
        self.last_interaction = None

    @classmethod
    @handle_exceptions
    async def get_user(cls, user_id: int) -> Optional['User']:
        """
        Get a user from the database by user_id.

        Args:
            user_id (int): Telegram user ID

        Returns:
            Optional[User]: User object if found, None otherwise

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        query = (
            "SELECT user_id, username, first_name, last_name, language_code, "
            "current_role_id, is_admin, created_at, last_interaction FROM users WHERE user_id = ?"
        )

        result = await execute_query_async(query, (user_id,))

        if not result:
            return None

        user = cls(
            user_id=result['user_id'],
            username=result['username'],
            first_name=result['first_name'],
            last_name=result['last_name'],
            language_code=result['language_code']
        )
        user.current_role_id = result['current_role_id']
        user.is_admin = bool(result['is_admin'])
        user.created_at = result['created_at']
        user.last_interaction = result['last_interaction']

        return user

    @handle_exceptions
    async def save(self) -> bool:
        """
        Save the user to the database.

        Returns:
            bool: True if successful, False otherwise

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        # Check if user already exists
        check_query = "SELECT user_id FROM users WHERE user_id = ?"
        existing_user = await execute_query_async(check_query, (self.user_id,))

        if existing_user:
            # Update existing user
            update_query = (
                "UPDATE users SET username = ?, first_name = ?, last_name = ?, "
                "language_code = ?, current_role_id = ?, last_interaction = CURRENT_TIMESTAMP "
                "WHERE user_id = ?"
            )
            update_params = (
                self.username, self.first_name, self.last_name,
                self.language_code, self.current_role_id, self.user_id
            )
            await execute_query_async(update_query, update_params)
        else:
            # Insert new user
            insert_query = (
                "INSERT INTO users (user_id, username, first_name, last_name, "
                "language_code, current_role_id) VALUES (?, ?, ?, ?, ?, ?)"
            )
            insert_params = (
                self.user_id, self.username, self.first_name, self.last_name,
                self.language_code, self.current_role_id
            )
            await execute_query_async(insert_query, insert_params)

            # Also create default preferences for new user
            prefs_query = "INSERT INTO user_preferences (user_id) VALUES (?)"
            await execute_query_async(prefs_query, (self.user_id,))

        logger.info(f"User {self.user_id} saved successfully")
        return True

    @handle_exceptions
    async def update_last_interaction(self) -> bool:
        """
        Update the user's last interaction timestamp.

        Returns:
            bool: True if successful, False otherwise

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        query = "UPDATE users SET last_interaction = CURRENT_TIMESTAMP WHERE user_id = ?"
        await execute_query_async(query, (self.user_id,))

        self.last_interaction = datetime.now().isoformat()
        return True

    @handle_exceptions
    async def set_current_role(self, role_id: int) -> bool:
        """
        Set the user's current role.

        Args:
            role_id (int): The role ID to set

        Returns:
            bool: True if successful, False otherwise

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        query = "UPDATE users SET current_role_id = ? WHERE user_id = ?"
        await execute_query_async(query, (role_id, self.user_id))

        self.current_role_id = role_id
        logger.info(f"Set current role for user {self.user_id} to {role_id}")
        return True

    @classmethod
    @handle_exceptions
    async def get_user_preferences(cls, user_id: int) -> Dict[str, Any]:
        """
        Get a user's preferences from the database.

        Args:
            user_id (int): Telegram user ID

        Returns:
            Dict[str, Any]: User preferences

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        query = (
            "SELECT language, response_length, formality_level, memory_enabled, voice_responses_enabled "
            "FROM user_preferences WHERE user_id = ?"
        )

        result = await execute_query_async(query, (user_id,))

        if result:
            return {
                "language": result['language'],
                "response_length": result['response_length'],
                "formality_level": result['formality_level'],
                "memory_enabled": bool(result['memory_enabled']),
                "voice_responses_enabled": bool(result['voice_responses_enabled']) if result['voice_responses_enabled'] is not None else False
            }

        # Return default preferences if not found
        return {
            "language": "en",
            "response_length": "medium",
            "formality_level": "casual",
            "memory_enabled": True,
            "voice_responses_enabled": False
        }

    @classmethod
    async def get_all_users(cls) -> List['User']:
        """
        Get all users from the database.

        Returns:
            List[User]: List of all users

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        query = (
            "SELECT user_id, username, first_name, last_name, language_code, "
            "current_role_id, is_admin, created_at, last_interaction FROM users"
        )

        results = await execute_query_async(query, fetch_all=True)

        users = []
        for result in results:
            user = cls(
                user_id=result['user_id'],
                username=result['username'],
                first_name=result['first_name'],
                last_name=result['last_name'],
                language_code=result['language_code']
            )
            user.current_role_id = result['current_role_id']
            user.is_admin = bool(result['is_admin'])
            user.created_at = result['created_at']
            user.last_interaction = result['last_interaction']
            users.append(user)

        return users

    @classmethod
    @handle_exceptions
    async def update_user_preferences(cls, user_id: int, preferences: Dict[str, Any]) -> bool:
        """
        Update a user's preferences in the database.

        Args:
            user_id (int): Telegram user ID
            preferences (Dict[str, Any]): User preferences to update

        Returns:
            bool: True if successful, False otherwise

        Raises:
            DatabaseException: If there's an error accessing the database
        """
        # Check if preferences exist
        check_query = "SELECT user_id FROM user_preferences WHERE user_id = ?"
        existing_prefs = await execute_query_async(check_query, (user_id,))

        # Prepare update fields
        update_fields = []
        update_values = []

        if "language" in preferences:
            update_fields.append("language = ?")
            update_values.append(preferences["language"])

        if "response_length" in preferences:
            update_fields.append("response_length = ?")
            update_values.append(preferences["response_length"])

        if "formality_level" in preferences:
            update_fields.append("formality_level = ?")
            update_values.append(preferences["formality_level"])

        if "memory_enabled" in preferences:
            update_fields.append("memory_enabled = ?")
            update_values.append(1 if preferences["memory_enabled"] else 0)

        if "voice_responses_enabled" in preferences:
            update_fields.append("voice_responses_enabled = ?")
            update_values.append(
                1 if preferences["voice_responses_enabled"] else 0)

        if not update_fields:
            logger.warning(f"No preferences to update for user {user_id}")
            return False

        if existing_prefs:
            # Update existing preferences
            query = f"UPDATE user_preferences SET {', '.join(update_fields)} WHERE user_id = ?"
            await execute_query_async(query, tuple(update_values + [user_id]))
        else:
            # Insert new preferences
            # First get default values
            default_prefs = await cls.get_user_preferences(user_id)

            # Override with provided values
            for key, value in preferences.items():
                default_prefs[key] = value

            # Insert with all values
            insert_query = (
                "INSERT INTO user_preferences (user_id, language, response_length, formality_level, memory_enabled, voice_responses_enabled) "
                "VALUES (?, ?, ?, ?, ?, ?)"
            )
            insert_params = (
                user_id,
                default_prefs["language"],
                default_prefs["response_length"],
                default_prefs["formality_level"],
                1 if default_prefs["memory_enabled"] else 0,
                1 if default_prefs["voice_responses_enabled"] else 0
            )
            await execute_query_async(insert_query, insert_params)

        logger.info(f"Updated preferences for user {user_id}")
        return True
