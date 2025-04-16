"""
Conversation model for Jyra
"""

import sqlite3
from typing import List, Dict, Any, Optional

from jyra.utils.config import DATABASE_PATH, MAX_CONVERSATION_HISTORY
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class Conversation:
    """
    Class for managing conversation data in the database.
    """

    @classmethod
    async def add_message(cls, user_id: int, role_id: int, user_message: str, bot_response: str) -> bool:
        """
        Add a message pair to the conversation history.

        Args:
            user_id (int): Telegram user ID
            role_id (int): Current role ID
            user_message (str): User's message
            bot_response (str): Bot's response

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "INSERT INTO conversations (user_id, role_id, user_message, bot_response) "
                "VALUES (?, ?, ?, ?)",
                (user_id, role_id, user_message, bot_response)
            )

            conn.commit()
            conn.close()

            logger.info(f"Added message to conversation for user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error adding message to conversation for user {user_id}: {str(e)}")
            return False

    @classmethod
    async def get_conversation_history(cls, user_id: int, role_id: Optional[int] = None,
                                       limit: int = MAX_CONVERSATION_HISTORY) -> List[Dict[str, Any]]:
        """
        Get conversation history for a user.

        Args:
            user_id (int): Telegram user ID
            role_id (Optional[int]): Filter by role ID
            limit (int): Maximum number of message pairs to retrieve

        Returns:
            List[Dict[str, Any]]: Conversation history
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            if role_id is not None:
                cursor.execute(
                    "SELECT user_message, bot_response, timestamp "
                    "FROM conversations "
                    "WHERE user_id = ? AND role_id = ? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (user_id, role_id, limit)
                )
            else:
                cursor.execute(
                    "SELECT user_message, bot_response, timestamp "
                    "FROM conversations "
                    "WHERE user_id = ? "
                    "ORDER BY timestamp DESC LIMIT ?",
                    (user_id, limit)
                )

            rows = cursor.fetchall()
            conn.close()

            # Convert to list of dictionaries and reverse to get chronological order
            history = []
            for row in reversed(rows):
                history.append({"role": "user", "content": row[0]})
                history.append({"role": "assistant", "content": row[1]})

            return history

        except Exception as e:
            logger.error(
                f"Error getting conversation history for user {user_id}: {str(e)}")
            return []

    @classmethod
    async def clear_conversation_history(cls, user_id: int) -> bool:
        """
        Clear conversation history for a user.

        Args:
            user_id (int): Telegram user ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM conversations WHERE user_id = ?",
                (user_id,)
            )

            conn.commit()
            conn.close()

            logger.info(f"Cleared conversation history for user {user_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error clearing conversation history for user {user_id}: {str(e)}")
            return False
