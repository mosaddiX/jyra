"""
Memory model for Jyra
"""

import sqlite3
from typing import List, Dict, Any, Optional

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class Memory:
    """
    Class for managing user memory data in the database.
    """

    def __init__(self, memory_id: Optional[int] = None, user_id: int = 0,
                 content: str = "", importance: int = 1):
        """
        Initialize a Memory object.

        Args:
            memory_id (Optional[int]): Memory ID
            user_id (int): User ID this memory belongs to
            content (str): Memory content
            importance (int): Importance level (1-5)
        """
        self.memory_id = memory_id
        self.user_id = user_id
        self.content = content
        self.importance = importance

    @classmethod
    async def add_memory(cls, user_id: int, content: str, importance: int = 1) -> bool:
        """
        Add a memory for a user.

        Args:
            user_id (int): User ID
            content (str): Memory content
            importance (int): Importance level (1-5)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if similar memory already exists
            cursor.execute(
                "SELECT memory_id FROM memories WHERE user_id = ? AND content = ?",
                (user_id, content)
            )

            existing_memory = cursor.fetchone()

            if existing_memory:
                # Update importance if memory already exists
                cursor.execute(
                    "UPDATE memories SET importance = ? WHERE memory_id = ?",
                    (importance, existing_memory[0])
                )
                logger.info(f"Updated existing memory for user {user_id}")
            else:
                # Insert new memory
                cursor.execute(
                    "INSERT INTO memories (user_id, content, importance) VALUES (?, ?, ?)",
                    (user_id, content, importance)
                )
                logger.info(f"Added new memory for user {user_id}")

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {str(e)}")
            return False

    @classmethod
    async def get_memories(cls, user_id: int, limit: Optional[int] = None) -> List['Memory']:
        """
        Get memories for a user.

        Args:
            user_id (int): User ID
            limit (Optional[int]): Maximum number of memories to retrieve

        Returns:
            List[Memory]: List of Memory objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            query = "SELECT memory_id, user_id, content, importance FROM memories WHERE user_id = ? ORDER BY importance DESC, created_at DESC"
            params = (user_id,)

            if limit is not None:
                query += " LIMIT ?"
                params = (user_id, limit)

            cursor.execute(query, params)

            rows = cursor.fetchall()
            conn.close()

            return [
                cls(
                    memory_id=row[0],
                    user_id=row[1],
                    content=row[2],
                    importance=row[3]
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(
                f"Error getting memories for user {user_id}: {str(e)}")
            return []

    @classmethod
    async def delete_memory(cls, memory_id: int, user_id: int) -> bool:
        """
        Delete a memory.

        Args:
            memory_id (int): Memory ID to delete
            user_id (int): User ID for permission check

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if memory exists and belongs to user
            cursor.execute(
                "SELECT user_id FROM memories WHERE memory_id = ?",
                (memory_id,)
            )

            row = cursor.fetchone()

            if not row:
                logger.warning(f"Memory {memory_id} not found for deletion")
                conn.close()
                return False

            memory_user_id = row[0]

            # Check if user has permission to delete this memory
            if memory_user_id != user_id:
                logger.warning(
                    f"User {user_id} does not have permission to delete memory {memory_id}")
                conn.close()
                return False

            # Delete the memory
            cursor.execute(
                "DELETE FROM memories WHERE memory_id = ?", (memory_id,))

            conn.commit()
            conn.close()

            logger.info(f"Memory {memory_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            return False

    @classmethod
    async def search_memories(cls, user_id: int, query: str) -> List['Memory']:
        """
        Search memories for a user.

        Args:
            user_id (int): User ID
            query (str): Search query

        Returns:
            List[Memory]: List of matching Memory objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Enable FTS if available
            cursor.execute("SELECT content FROM memories WHERE user_id = ? AND content LIKE ?",
                           (user_id, f"%{query}%"))

            rows = cursor.fetchall()

            # Get full memory objects for matches
            memories = []
            for row in rows:
                content = row[0]
                cursor.execute(
                    "SELECT memory_id, user_id, content, importance FROM memories WHERE user_id = ? AND content = ?",
                    (user_id, content)
                )
                memory_row = cursor.fetchone()
                if memory_row:
                    memories.append(cls(
                        memory_id=memory_row[0],
                        user_id=memory_row[1],
                        content=memory_row[2],
                        importance=memory_row[3]
                    ))

            conn.close()

            return memories

        except Exception as e:
            logger.error(
                f"Error searching memories for user {user_id}: {str(e)}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the memory to a dictionary.

        Returns:
            Dict[str, Any]: Memory data as a dictionary
        """
        return {
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "content": self.content,
            "importance": self.importance
        }
