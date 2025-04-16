"""
Memory model for Jyra
"""

import sqlite3
from typing import List, Dict, Any, Optional

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger
from jyra.ai.memory_extractor import memory_extractor

logger = setup_logger(__name__)


class Memory:
    """
    Class for managing user memory data in the database.
    """

    def __init__(self, memory_id: Optional[int] = None, user_id: int = 0,
                 content: str = "", category: str = "general", importance: int = 1,
                 source: str = "explicit", context: Optional[str] = None,
                 last_accessed: Optional[str] = None, created_at: Optional[str] = None):
        """
        Initialize a Memory object.

        Args:
            memory_id (Optional[int]): Memory ID
            user_id (int): User ID this memory belongs to
            content (str): Memory content
            category (str): Category of the memory (e.g., 'personal', 'preferences', 'facts')
            importance (int): Importance level (1-5)
            source (str): Source of the memory ('explicit', 'extracted', 'inferred')
            context (Optional[str]): Context in which the memory was created
            last_accessed (Optional[str]): When the memory was last accessed
            created_at (Optional[str]): When the memory was created
        """
        self.memory_id = memory_id
        self.user_id = user_id
        self.content = content
        self.category = category
        self.importance = importance
        self.source = source
        self.context = context
        self.last_accessed = last_accessed
        self.created_at = created_at

    @classmethod
    async def add_memory(cls, user_id: int, content: str, category: str = "general",
                         importance: int = 1, source: str = "explicit",
                         context: Optional[str] = None) -> bool:
        """
        Add a memory for a user.

        Args:
            user_id (int): User ID
            content (str): Memory content
            category (str): Category of the memory
            importance (int): Importance level (1-5)
            source (str): Source of the memory ('explicit', 'extracted', 'inferred')
            context (Optional[str]): Context in which the memory was created

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
                # Update importance and last_accessed if memory already exists
                cursor.execute(
                    "UPDATE memories SET importance = ?, last_accessed = CURRENT_TIMESTAMP WHERE memory_id = ?",
                    (importance, existing_memory[0])
                )
                logger.info(f"Updated existing memory for user {user_id}")
            else:
                # Insert new memory
                cursor.execute(
                    """INSERT INTO memories
                       (user_id, content, category, importance, source, context, last_accessed)
                       VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, content, category, importance, source, context)
                )
                logger.info(
                    f"Added new memory for user {user_id} in category '{category}'")

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {str(e)}")
            return False

    @classmethod
    async def get_memories(cls, user_id: int, category: Optional[str] = None,
                           limit: Optional[int] = None, min_importance: int = 0) -> List['Memory']:
        """
        Get memories for a user.

        Args:
            user_id (int): User ID
            category (Optional[str]): Filter by category
            limit (Optional[int]): Maximum number of memories to retrieve
            min_importance (int): Minimum importance level (0-5)

        Returns:
            List[Memory]: List of Memory objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            query = """SELECT memory_id, user_id, content, category, importance, source, context,
                       last_accessed, created_at
                       FROM memories WHERE user_id = ? AND importance >= ?"""
            params = [user_id, min_importance]

            if category is not None:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY importance DESC, last_accessed DESC"

            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)

            rows = cursor.fetchall()
            conn.close()

            # Update last_accessed for retrieved memories
            await cls._update_last_accessed([row[0] for row in rows])

            return [
                cls(
                    memory_id=row[0],
                    user_id=row[1],
                    content=row[2],
                    category=row[3],
                    importance=row[4],
                    source=row[5],
                    context=row[6],
                    last_accessed=row[7],
                    created_at=row[8]
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

    @classmethod
    async def _update_last_accessed(cls, memory_ids: List[int]) -> None:
        """
        Update the last_accessed timestamp for a list of memories.

        Args:
            memory_ids (List[int]): List of memory IDs to update
        """
        if not memory_ids:
            return

        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Update last_accessed for each memory
            for memory_id in memory_ids:
                cursor.execute(
                    "UPDATE memories SET last_accessed = CURRENT_TIMESTAMP WHERE memory_id = ?",
                    (memory_id,)
                )

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(
                f"Error updating last_accessed for memories: {str(e)}")

    @classmethod
    async def extract_memories_from_message(cls, user_id: int, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract potential memories from user messages using AI.

        Args:
            user_id (int): User ID
            text (str): Text to extract memories from
            context (Optional[Dict[str, Any]]): Additional context about the user

        Returns:
            List[Dict[str, Any]]: List of extracted memories with category, importance, and content
        """
        try:
            # Use the memory extractor to get memories
            extracted_memories = await memory_extractor.extract_memories(text, context)

            # Store each extracted memory
            for memory in extracted_memories:
                await cls.add_memory(
                    user_id=user_id,
                    content=memory["content"],
                    category=memory["category"],
                    importance=memory["importance"],
                    source="extracted",
                    context=f"Extracted from message: {text[:100]}..."
                )

            return extracted_memories
        except Exception as e:
            logger.error(
                f"Error extracting memories from message for user {user_id}: {str(e)}")
            return []

    @classmethod
    async def get_memory_summary(cls, user_id: int, category: Optional[str] = None) -> str:
        """
        Get a summary of memories for a user.

        Args:
            user_id (int): User ID
            category (Optional[str]): Filter by category

        Returns:
            str: Summary of memories
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            query = "SELECT summary FROM memory_summaries WHERE user_id = ?"
            params = [user_id]

            if category is not None:
                query += " AND category = ?"
                params.append(category)

            query += " ORDER BY last_updated DESC LIMIT 1"

            cursor.execute(query, params)
            row = cursor.fetchone()
            conn.close()

            if row:
                return row[0]
            return ""

        except Exception as e:
            logger.error(
                f"Error getting memory summary for user {user_id}: {str(e)}")
            return ""

    @classmethod
    async def update_memory_summary(cls, user_id: int, category: str, summary: str) -> bool:
        """
        Update or create a memory summary for a user.

        Args:
            user_id (int): User ID
            category (str): Category of the summary
            summary (str): Summary text

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if summary already exists
            cursor.execute(
                "SELECT summary_id FROM memory_summaries WHERE user_id = ? AND category = ?",
                (user_id, category)
            )

            existing_summary = cursor.fetchone()

            if existing_summary:
                # Update existing summary
                cursor.execute(
                    "UPDATE memory_summaries SET summary = ?, last_updated = CURRENT_TIMESTAMP WHERE summary_id = ?",
                    (summary, existing_summary[0])
                )
            else:
                # Insert new summary
                cursor.execute(
                    "INSERT INTO memory_summaries (user_id, category, summary) VALUES (?, ?, ?)",
                    (user_id, category, summary)
                )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(
                f"Error updating memory summary for user {user_id}: {str(e)}")
            return False

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
            "category": self.category,
            "importance": self.importance,
            "source": self.source,
            "context": self.context,
            "last_accessed": self.last_accessed,
            "created_at": self.created_at
        }
