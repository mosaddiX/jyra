"""
User model for Jyra
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from jyra.utils.config import DATABASE_PATH
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
    async def get_user(cls, user_id: int) -> Optional['User']:
        """
        Get a user from the database by user_id.

        Args:
            user_id (int): Telegram user ID

        Returns:
            Optional[User]: User object if found, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT user_id, username, first_name, last_name, language_code, "
                "current_role_id, is_admin, created_at, last_interaction FROM users WHERE user_id = ?",
                (user_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                user = cls(
                    user_id=row[0],
                    username=row[1],
                    first_name=row[2],
                    last_name=row[3],
                    language_code=row[4]
                )
                user.current_role_id = row[5]
                user.is_admin = bool(row[6])
                user.created_at = row[7]
                user.last_interaction = row[8]
                return user

            return None

        except Exception as e:
            logger.error(f"Error getting user {user_id}: {str(e)}")
            return None

    async def save(self) -> bool:
        """
        Save the user to the database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if user already exists
            cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?", (self.user_id,))
            existing_user = cursor.fetchone()

            if existing_user:
                # Update existing user
                cursor.execute(
                    "UPDATE users SET username = ?, first_name = ?, last_name = ?, "
                    "language_code = ?, current_role_id = ?, last_interaction = CURRENT_TIMESTAMP "
                    "WHERE user_id = ?",
                    (self.username, self.first_name, self.last_name,
                     self.language_code, self.current_role_id, self.user_id)
                )
            else:
                # Insert new user
                cursor.execute(
                    "INSERT INTO users (user_id, username, first_name, last_name, "
                    "language_code, current_role_id) VALUES (?, ?, ?, ?, ?, ?)",
                    (self.user_id, self.username, self.first_name, self.last_name,
                     self.language_code, self.current_role_id)
                )

                # Also create default preferences for new user
                cursor.execute(
                    "INSERT INTO user_preferences (user_id) VALUES (?)",
                    (self.user_id,)
                )

            conn.commit()
            conn.close()

            logger.info(f"User {self.user_id} saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving user {self.user_id}: {str(e)}")
            return False

    async def update_last_interaction(self) -> bool:
        """
        Update the user's last interaction timestamp.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE users SET last_interaction = CURRENT_TIMESTAMP WHERE user_id = ?",
                (self.user_id,)
            )

            conn.commit()
            conn.close()

            self.last_interaction = datetime.now().isoformat()
            return True

        except Exception as e:
            logger.error(
                f"Error updating last interaction for user {self.user_id}: {str(e)}")
            return False

    async def set_current_role(self, role_id: int) -> bool:
        """
        Set the user's current role.

        Args:
            role_id (int): The role ID to set

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE users SET current_role_id = ? WHERE user_id = ?",
                (role_id, self.user_id)
            )

            conn.commit()
            conn.close()

            self.current_role_id = role_id
            logger.info(
                f"Set current role for user {self.user_id} to {role_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error setting current role for user {self.user_id}: {str(e)}")
            return False

    @classmethod
    async def get_user_preferences(cls, user_id: int) -> Dict[str, Any]:
        """
        Get a user's preferences from the database.

        Args:
            user_id (int): Telegram user ID

        Returns:
            Dict[str, Any]: User preferences
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT language, response_length, formality_level, memory_enabled, voice_responses_enabled "
                "FROM user_preferences WHERE user_id = ?",
                (user_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    "language": row[0],
                    "response_length": row[1],
                    "formality_level": row[2],
                    "memory_enabled": bool(row[3]),
                    "voice_responses_enabled": bool(row[4]) if row[4] is not None else False
                }

            # Return default preferences if not found
            return {
                "language": "en",
                "response_length": "medium",
                "formality_level": "casual",
                "memory_enabled": True,
                "voice_responses_enabled": False
            }

        except Exception as e:
            logger.error(
                f"Error getting preferences for user {user_id}: {str(e)}")
            return {
                "language": "en",
                "response_length": "medium",
                "formality_level": "casual",
                "memory_enabled": True,
                "voice_responses_enabled": False
            }

    @classmethod
    async def update_user_preferences(cls, user_id: int, preferences: Dict[str, Any]) -> bool:
        """
        Update a user's preferences in the database.

        Args:
            user_id (int): Telegram user ID
            preferences (Dict[str, Any]): User preferences to update

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if preferences exist
            cursor.execute(
                "SELECT user_id FROM user_preferences WHERE user_id = ?", (user_id,))
            existing_prefs = cursor.fetchone()

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
                cursor.execute(query, tuple(update_values + [user_id]))
            else:
                # Insert new preferences
                # First get default values
                default_prefs = await cls.get_user_preferences(user_id)

                # Override with provided values
                for key, value in preferences.items():
                    default_prefs[key] = value

                # Insert with all values
                cursor.execute(
                    "INSERT INTO user_preferences (user_id, language, response_length, formality_level, memory_enabled, voice_responses_enabled) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, default_prefs["language"], default_prefs["response_length"],
                     default_prefs["formality_level"], 1 if default_prefs["memory_enabled"] else 0,
                     1 if default_prefs["voice_responses_enabled"] else 0)
                )

            conn.commit()
            conn.close()

            logger.info(f"Updated preferences for user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error updating preferences for user {user_id}: {str(e)}")
            return False
