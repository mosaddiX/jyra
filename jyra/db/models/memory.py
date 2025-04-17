"""
Memory model for Jyra
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set, Tuple, Union

from jyra.utils.config import DATABASE_PATH
from jyra.utils.exceptions import DatabaseException
from jyra.utils.logger import setup_logger
from jyra.ai.memory_extractor import memory_extractor
from jyra.ai.embeddings.embedding_generator import embedding_generator
from jyra.ai.embeddings.vector_db import vector_db
from jyra.db.models.memory_semantic import semantic_search, get_memory_by_id, generate_embeddings_for_all_memories, update_memory_embedding

logger = setup_logger(__name__)


class Memory:
    """
    Class for managing user memory data in the database.
    """

    def __init__(self, memory_id: Optional[int] = None, user_id: int = 0,
                 content: str = "", category: str = "general", importance: int = 1,
                 source: str = "explicit", context: Optional[str] = None,
                 last_accessed: Optional[str] = None, created_at: Optional[str] = None,
                 confidence: float = 1.0, expires_at: Optional[str] = None,
                 recall_count: int = 0, last_reinforced: Optional[str] = None,
                 is_consolidated: bool = False, tags: Optional[List[str]] = None):
        """
        Initialize a Memory object.

        Args:
            memory_id (Optional[int]): Memory ID
            user_id (int): User ID this memory belongs to
            content (str): Memory content
            category (str): Category of the memory (e.g., 'personal', 'preferences', 'facts')
            importance (int): Importance level (1-5)
            source (str): Source of the memory ('explicit', 'extracted', 'inferred', 'consolidated')
            context (Optional[str]): Context in which the memory was created
            last_accessed (Optional[str]): When the memory was last accessed
            created_at (Optional[str]): When the memory was created
            confidence (float): Confidence level in the memory's accuracy (0.0-1.0)
            expires_at (Optional[str]): When the memory expires (if temporary)
            recall_count (int): Number of times this memory has been recalled
            last_reinforced (Optional[str]): When the memory was last reinforced
            is_consolidated (bool): Whether this memory is a result of consolidation
            tags (Optional[List[str]]): Tags associated with this memory
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
        self.confidence = confidence
        self.expires_at = expires_at
        self.recall_count = recall_count
        self.last_reinforced = last_reinforced
        self.is_consolidated = is_consolidated
        self.tags = tags or []

    async def save(self) -> Optional[int]:
        """
        Save this memory to the database.

        Returns:
            Optional[int]: Memory ID if successful, None otherwise
        """
        return await Memory.add_memory(
            user_id=self.user_id,
            content=self.content,
            category=self.category,
            importance=self.importance,
            source=self.source,
            context=self.context,
            confidence=self.confidence,
            expires_at=self.expires_at,
            tags=self.tags,
            is_consolidated=self.is_consolidated
        )

    @classmethod
    async def add_memory(cls, user_id: int, content: str, category: str = "general",
                         importance: int = 1, source: str = "explicit",
                         context: Optional[str] = None, confidence: float = 1.0,
                         expires_at: Optional[str] = None, tags: Optional[List[str]] = None,
                         is_consolidated: bool = False) -> Optional[int]:
        """
        Add a memory for a user.

        Args:
            user_id (int): User ID
            content (str): Memory content
            category (str): Category of the memory
            importance (int): Importance level (1-5)
            source (str): Source of the memory ('explicit', 'extracted', 'inferred', 'consolidated')
            context (Optional[str]): Context in which the memory was created
            confidence (float): Confidence level in the memory's accuracy (0.0-1.0)
            expires_at (Optional[str]): When the memory expires (if temporary)
            tags (Optional[List[str]]): Tags associated with this memory
            is_consolidated (bool): Whether this memory is a result of consolidation

        Returns:
            Optional[int]: Memory ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if similar memory already exists
            cursor.execute(
                "SELECT memory_id, importance, confidence, recall_count FROM memories WHERE user_id = ? AND content = ?",
                (user_id, content)
            )

            existing_memory = cursor.fetchone()

            memory_id = None

            if existing_memory:
                memory_id = existing_memory[0]
                old_importance = existing_memory[1]
                old_confidence = existing_memory[2]
                recall_count = existing_memory[3] + 1

                # Update memory with reinforcement
                # If the same memory is encountered again, increase its importance and confidence
                new_importance = max(old_importance, importance)
                # Gradually increase confidence
                new_confidence = min(1.0, old_confidence + (confidence * 0.1))

                cursor.execute(
                    """UPDATE memories SET
                       importance = ?,
                       confidence = ?,
                       recall_count = ?,
                       last_accessed = CURRENT_TIMESTAMP,
                       last_reinforced = CURRENT_TIMESTAMP
                       WHERE memory_id = ?""",
                    (new_importance, new_confidence, recall_count, memory_id)
                )
                logger.info(
                    f"Updated existing memory for user {user_id} (reinforced)")
            else:
                # Insert new memory
                cursor.execute(
                    """INSERT INTO memories
                       (user_id, content, category, importance, source, context,
                        confidence, expires_at, is_consolidated, last_accessed)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                    (user_id, content, category, importance, source, context,
                     confidence, expires_at, 1 if is_consolidated else 0)
                )
                memory_id = cursor.lastrowid
                logger.info(
                    f"Added new memory for user {user_id} in category '{category}'")

            # Add tags if provided
            if tags and memory_id:
                for tag_name in tags:
                    # Get or create tag
                    cursor.execute(
                        "SELECT tag_id FROM memory_tags WHERE user_id = ? AND tag_name = ?",
                        (user_id, tag_name)
                    )
                    tag_row = cursor.fetchone()

                    if tag_row:
                        tag_id = tag_row[0]
                    else:
                        cursor.execute(
                            "INSERT INTO memory_tags (user_id, tag_name) VALUES (?, ?)",
                            (user_id, tag_name)
                        )
                        tag_id = cursor.lastrowid

                    # Associate tag with memory
                    try:
                        cursor.execute(
                            "INSERT INTO memory_tag_associations (memory_id, tag_id) VALUES (?, ?)",
                            (memory_id, tag_id)
                        )
                    except sqlite3.IntegrityError:
                        # Tag association already exists
                        pass

            conn.commit()
            conn.close()

            # Generate and store embedding for the memory
            if memory_id:
                try:
                    # Generate embedding
                    embedding = await embedding_generator.generate_embedding(content)

                    # Store embedding
                    await vector_db.store_embedding(memory_id, embedding)
                except Exception as e:
                    logger.error(
                        f"Error generating/storing embedding for memory {memory_id}: {str(e)}")

            return memory_id

        except Exception as e:
            logger.error(f"Error adding memory for user {user_id}: {str(e)}")
            return None

    @classmethod
    async def get_memories(cls, user_id: int, category: Optional[str] = None,
                           limit: Optional[int] = None, min_importance: int = 0,
                           max_importance: Optional[int] = None, min_confidence: float = 0.0,
                           include_expired: bool = False, tags: Optional[List[str]] = None,
                           sort_by: str = "importance") -> List['Memory']:
        """
        Get memories for a user with enhanced filtering options.

        Args:
            user_id (int): User ID
            category (Optional[str]): Filter by category
            limit (Optional[int]): Maximum number of memories to retrieve
            min_importance (int): Minimum importance level (0-5)
            max_importance (Optional[int]): Maximum importance level (0-5)
            min_confidence (float): Minimum confidence level (0.0-1.0)
            include_expired (bool): Whether to include expired memories
            tags (Optional[List[str]]): Filter by tags (memories must have ALL specified tags)
            sort_by (str): Field to sort by ('importance', 'confidence', 'recency', 'recall_count')

        Returns:
            List[Memory]: List of Memory objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Base query with all fields
            query = """SELECT m.memory_id, m.user_id, m.content, m.category, m.importance,
                       m.source, m.context, m.last_accessed, m.created_at, m.confidence,
                       m.expires_at, m.recall_count, m.last_reinforced, m.is_consolidated
                       FROM memories m"""

            # Add tag join if filtering by tags
            if tags and len(tags) > 0:
                query += """
                    JOIN memory_tag_associations mta ON m.memory_id = mta.memory_id
                    JOIN memory_tags mt ON mta.tag_id = mt.tag_id
                """

            # Start WHERE clause
            query += " WHERE m.user_id = ? AND m.importance >= ? AND m.confidence >= ?"
            params = [user_id, min_importance, min_confidence]

            # Add category filter if specified
            if category is not None:
                query += " AND m.category = ?"
                params.append(category)

            # Add max importance filter if specified
            if max_importance is not None:
                query += " AND m.importance <= ?"
                params.append(max_importance)

            # Filter out expired memories unless explicitly included
            if not include_expired:
                query += " AND (m.expires_at IS NULL OR m.expires_at > CURRENT_TIMESTAMP)"

            # Add tag filtering if specified
            if tags and len(tags) > 0:
                placeholders = ", ".join(["?" for _ in tags])
                query += f" AND mt.tag_name IN ({placeholders})"
                params.extend(tags)

                # Group to ensure all tags are matched if multiple tags are specified
                query += " GROUP BY m.memory_id HAVING COUNT(DISTINCT mt.tag_name) = ?"
                params.append(len(tags))

            # Add sorting based on the specified field
            if sort_by == "confidence":
                query += " ORDER BY m.confidence DESC, m.importance DESC"
            elif sort_by == "recency":
                query += " ORDER BY m.last_accessed DESC"
            elif sort_by == "recall_count":
                query += " ORDER BY m.recall_count DESC, m.importance DESC"
            else:  # Default to importance
                query += " ORDER BY m.importance DESC, m.last_accessed DESC"

            # Add limit if specified
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Get tags for each memory
            memory_tags = {}
            if rows:
                memory_ids = [row[0] for row in rows]
                placeholders = ", ".join(["?" for _ in memory_ids])
                tag_query = f"""
                    SELECT mta.memory_id, mt.tag_name
                    FROM memory_tag_associations mta
                    JOIN memory_tags mt ON mta.tag_id = mt.tag_id
                    WHERE mta.memory_id IN ({placeholders})
                """
                cursor.execute(tag_query, memory_ids)
                tag_rows = cursor.fetchall()

                for memory_id, tag_name in tag_rows:
                    if memory_id not in memory_tags:
                        memory_tags[memory_id] = []
                    memory_tags[memory_id].append(tag_name)

            conn.close()

            # Update last_accessed for retrieved memories
            await cls._update_last_accessed([row[0] for row in rows])

            # Create Memory objects with all fields
            memories = []
            for row in rows:
                memory_id = row[0]
                memory = cls(
                    memory_id=memory_id,
                    user_id=row[1],
                    content=row[2],
                    category=row[3],
                    importance=row[4],
                    source=row[5],
                    context=row[6],
                    last_accessed=row[7],
                    created_at=row[8],
                    confidence=row[9],
                    expires_at=row[10],
                    recall_count=row[11],
                    last_reinforced=row[12],
                    is_consolidated=bool(row[13]),
                    tags=memory_tags.get(memory_id, [])
                )
                memories.append(memory)

            return memories

        except Exception as e:
            logger.error(
                f"Error getting memories for user {user_id}: {str(e)}")
            return []

    @classmethod
    async def get_memory_by_id(cls, user_id: int, memory_id: int) -> Optional['Memory']:
        """
        Get a memory by ID.

        Args:
            user_id (int): User ID for permission check
            memory_id (int): Memory ID to retrieve

        Returns:
            Optional[Memory]: Memory object if found, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Get memory details
            cursor.execute(
                """SELECT memory_id, user_id, content, category, importance, source, context,
                          last_accessed, created_at, confidence, expires_at, recall_count,
                          last_reinforced, is_consolidated
                   FROM memories WHERE memory_id = ? AND user_id = ?""",
                (memory_id, user_id)
            )

            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            # Get tags for this memory
            tags = await cls._get_memory_tags(memory_id)

            # Update last_accessed
            await cls._update_last_accessed([memory_id])

            # Create Memory object
            memory = cls(
                memory_id=row[0],
                user_id=row[1],
                content=row[2],
                category=row[3],
                importance=row[4],
                source=row[5],
                context=row[6],
                last_accessed=row[7],
                created_at=row[8],
                confidence=row[9],
                expires_at=row[10],
                recall_count=row[11],
                last_reinforced=row[12],
                is_consolidated=bool(row[13]),
                tags=tags
            )

            return memory

        except Exception as e:
            logger.error(f"Error getting memory {memory_id}: {str(e)}")
            return None

    @classmethod
    async def mark_as_consolidated(cls, memory_id: int, consolidated_memory_id: int) -> bool:
        """
        Mark a memory as consolidated into another memory.

        Args:
            memory_id (int): Memory ID to mark as consolidated
            consolidated_memory_id (int): ID of the consolidated memory

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Update the memory to mark it as consolidated
            cursor.execute(
                """UPDATE memories SET
                   is_consolidated = 1,
                   context = CASE
                       WHEN context IS NULL THEN ?
                       ELSE context || ' | ' || ?
                   END
                   WHERE memory_id = ?""",
                (f"Consolidated into memory {consolidated_memory_id}",
                 f"Consolidated into memory {consolidated_memory_id}",
                 memory_id)
            )

            # Create a relationship between the original and consolidated memories
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS memory_consolidations (
                   original_memory_id INTEGER,
                   consolidated_memory_id INTEGER,
                   consolidated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                   PRIMARY KEY (original_memory_id, consolidated_memory_id),
                   FOREIGN KEY (original_memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE,
                   FOREIGN KEY (consolidated_memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE
                )"""
            )

            cursor.execute(
                "INSERT OR IGNORE INTO memory_consolidations (original_memory_id, consolidated_memory_id) VALUES (?, ?)",
                (memory_id, consolidated_memory_id)
            )

            conn.commit()
            conn.close()

            logger.info(
                f"Memory {memory_id} marked as consolidated into memory {consolidated_memory_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error marking memory {memory_id} as consolidated: {str(e)}")
            return False

    @classmethod
    async def get_consolidated_memories(cls, consolidated_memory_id: int) -> List['Memory']:
        """
        Get the original memories that were consolidated into a consolidated memory.

        Args:
            consolidated_memory_id (int): ID of the consolidated memory

        Returns:
            List[Memory]: List of original memories
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Get the original memory IDs
            cursor.execute(
                """SELECT original_memory_id FROM memory_consolidations
                   WHERE consolidated_memory_id = ?""",
                (consolidated_memory_id,)
            )

            original_memory_ids = [row[0] for row in cursor.fetchall()]
            conn.close()

            if not original_memory_ids:
                return []

            # Get the memory objects
            memories = []
            for memory_id in original_memory_ids:
                # Get memory directly from database without user_id check
                try:
                    conn = sqlite3.connect(DATABASE_PATH)
                    cursor = conn.cursor()

                    cursor.execute(
                        """SELECT memory_id, user_id, content, category, importance, source, context,
                                  last_accessed, created_at, confidence, expires_at, recall_count,
                                  last_reinforced, is_consolidated
                           FROM memories WHERE memory_id = ?""",
                        (memory_id,)
                    )

                    row = cursor.fetchone()
                    conn.close()

                    if row:
                        # Get tags for this memory
                        tags = await cls._get_memory_tags(memory_id)

                        memory = cls(
                            memory_id=row[0],
                            user_id=row[1],
                            content=row[2],
                            category=row[3],
                            importance=row[4],
                            source=row[5],
                            context=row[6],
                            last_accessed=row[7],
                            created_at=row[8],
                            confidence=row[9],
                            expires_at=row[10],
                            recall_count=row[11],
                            last_reinforced=row[12],
                            is_consolidated=bool(row[13]),
                            tags=tags
                        )
                        memories.append(memory)
                except Exception as e:
                    logger.error(
                        f"Error getting consolidated memory {memory_id}: {str(e)}")

            return memories

        except Exception as e:
            logger.error(
                f"Error getting consolidated memories for {consolidated_memory_id}: {str(e)}")
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

            # Also delete the embedding if it exists
            cursor.execute(
                "DELETE FROM memory_embeddings WHERE memory_id = ?", (memory_id,))

            # Also delete any consolidation relationships
            cursor.execute(
                "DELETE FROM memory_consolidations WHERE original_memory_id = ? OR consolidated_memory_id = ?",
                (memory_id, memory_id)
            )

            conn.commit()
            conn.close()

            logger.info(f"Memory {memory_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting memory {memory_id}: {str(e)}")
            return False

    @classmethod
    async def search_memories(cls, user_id: int, query: str, limit: Optional[int] = 10,
                              use_semantic: bool = True) -> List['Memory']:
        """
        Search memories for a user using keyword or semantic search.

        Args:
            user_id (int): User ID
            query (str): Search query
            limit (Optional[int]): Maximum number of memories to retrieve
            use_semantic (bool): Whether to use semantic search

        Returns:
            List[Memory]: List of matching Memory objects
        """
        try:
            if use_semantic:
                # Use semantic search
                memory_dicts = await semantic_search(user_id, query, limit)

                # Convert to Memory objects
                memories = []
                for memory_dict in memory_dicts:
                    memory = cls(
                        memory_id=memory_dict["memory_id"],
                        user_id=memory_dict["user_id"],
                        content=memory_dict["content"],
                        category=memory_dict["category"],
                        importance=memory_dict["importance"],
                        source=memory_dict["source"],
                        context=memory_dict["context"],
                        last_accessed=memory_dict["last_accessed"],
                        created_at=memory_dict["created_at"],
                        confidence=memory_dict["confidence"],
                        expires_at=memory_dict["expires_at"],
                        recall_count=memory_dict["recall_count"],
                        last_reinforced=memory_dict["last_reinforced"],
                        is_consolidated=memory_dict["is_consolidated"],
                        tags=memory_dict["tags"]
                    )
                    memories.append(memory)

                return memories
            else:
                # Use keyword search
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()

                # Use LIKE for simple text search
                search_query = f"%{query}%"

                query_sql = """SELECT memory_id, user_id, content, category, importance, source, context,
                               last_accessed, created_at, confidence, expires_at, recall_count,
                               last_reinforced, is_consolidated
                               FROM memories WHERE user_id = ? AND content LIKE ?"""
                params = [user_id, search_query]

                if limit is not None:
                    query_sql += " LIMIT ?"
                    params.append(limit)

                cursor.execute(query_sql, params)
                rows = cursor.fetchall()

                # Update last_accessed for retrieved memories
                await cls._update_last_accessed([row[0] for row in rows])

                # Get tags for each memory
                memories = []
                for row in rows:
                    memory_id = row[0]
                    tags = await cls._get_memory_tags(memory_id)

                    memory = cls(
                        memory_id=memory_id,
                        user_id=row[1],
                        content=row[2],
                        category=row[3],
                        importance=row[4],
                        source=row[5],
                        context=row[6],
                        last_accessed=row[7],
                        created_at=row[8],
                        confidence=row[9],
                        expires_at=row[10],
                        recall_count=row[11],
                        last_reinforced=row[12],
                        is_consolidated=bool(row[13]),
                        tags=tags
                    )
                    memories.append(memory)

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
    async def _get_memory_tags(cls, memory_id: int) -> List[str]:
        """
        Get tags for a memory.

        Args:
            memory_id (int): Memory ID

        Returns:
            List[str]: List of tags
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """SELECT mt.tag_name
                   FROM memory_tag_associations mta
                   JOIN memory_tags mt ON mta.tag_id = mt.tag_id
                   WHERE mta.memory_id = ?""",
                (memory_id,)
            )

            tags = [row[0] for row in cursor.fetchall()]
            conn.close()

            return tags

        except Exception as e:
            logger.error(
                f"Error getting tags for memory {memory_id}: {str(e)}")
            return []

    @classmethod
    async def extract_memories_from_message(cls, user_id: int, text: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract potential memories from user messages using AI with enhanced fields.

        Args:
            user_id (int): User ID
            text (str): Text to extract memories from
            context (Optional[Dict[str, Any]]): Additional context about the user

        Returns:
            List[Dict[str, Any]]: List of extracted memories with enhanced fields
        """
        try:
            # Use the memory extractor to get memories with enhanced fields
            extracted_memories = await memory_extractor.extract_memories(text, context)

            # Store each extracted memory with enhanced fields
            for memory in extracted_memories:
                await cls.add_memory(
                    user_id=user_id,
                    content=memory["content"],
                    category=memory["category"],
                    importance=memory["importance"],
                    source="extracted",
                    context=f"Extracted from message: {text[:100]}...",
                    confidence=memory.get("confidence", 0.8),
                    expires_at=memory.get("expires_at"),
                    tags=memory.get("tags", [])
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
            "created_at": self.created_at,
            "confidence": self.confidence,
            "expires_at": self.expires_at,
            "recall_count": self.recall_count,
            "last_reinforced": self.last_reinforced,
            "is_consolidated": self.is_consolidated,
            "tags": self.tags
        }

    @classmethod
    async def add_memory_relationship(cls, source_memory_id: int, target_memory_id: int,
                                      relationship_type: str, strength: float = 1.0) -> bool:
        """
        Add a relationship between two memories.

        Args:
            source_memory_id (int): Source memory ID
            target_memory_id (int): Target memory ID
            relationship_type (str): Type of relationship (e.g., 'contradicts', 'supports', 'relates_to')
            strength (float): Strength of the relationship (0.0-1.0)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if relationship already exists
            cursor.execute(
                """SELECT relationship_id FROM memory_relationships
                   WHERE source_memory_id = ? AND target_memory_id = ? AND relationship_type = ?""",
                (source_memory_id, target_memory_id, relationship_type)
            )

            existing_relationship = cursor.fetchone()

            if existing_relationship:
                # Update existing relationship
                cursor.execute(
                    """UPDATE memory_relationships SET strength = ?
                       WHERE source_memory_id = ? AND target_memory_id = ? AND relationship_type = ?""",
                    (strength, source_memory_id, target_memory_id, relationship_type)
                )
            else:
                # Insert new relationship
                cursor.execute(
                    """INSERT INTO memory_relationships
                       (source_memory_id, target_memory_id, relationship_type, strength)
                       VALUES (?, ?, ?, ?)""",
                    (source_memory_id, target_memory_id,
                     relationship_type, strength)
                )

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(f"Error adding memory relationship: {str(e)}")
            return False

    @classmethod
    async def get_related_memories(cls, memory_id: int, relationship_type: Optional[str] = None,
                                   min_strength: float = 0.0) -> List[Dict[str, Any]]:
        """
        Get memories related to a specific memory.

        Args:
            memory_id (int): Memory ID to find relations for
            relationship_type (Optional[str]): Filter by relationship type
            min_strength (float): Minimum relationship strength (0.0-1.0)

        Returns:
            List[Dict[str, Any]]: List of related memories with relationship info
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Query for outgoing relationships (source -> target)
            outgoing_query = """SELECT m.*, r.relationship_type, r.strength, 'outgoing' as direction
                              FROM memories m
                              JOIN memory_relationships r ON m.memory_id = r.target_memory_id
                              WHERE r.source_memory_id = ? AND r.strength >= ?"""
            outgoing_params = [memory_id, min_strength]

            # Query for incoming relationships (target <- source)
            incoming_query = """SELECT m.*, r.relationship_type, r.strength, 'incoming' as direction
                              FROM memories m
                              JOIN memory_relationships r ON m.memory_id = r.source_memory_id
                              WHERE r.target_memory_id = ? AND r.strength >= ?"""
            incoming_params = [memory_id, min_strength]

            # Add relationship type filter if specified
            if relationship_type is not None:
                outgoing_query += " AND r.relationship_type = ?"
                outgoing_params.append(relationship_type)
                incoming_query += " AND r.relationship_type = ?"
                incoming_params.append(relationship_type)

            # Execute queries
            cursor.execute(outgoing_query, outgoing_params)
            outgoing_rows = cursor.fetchall()

            cursor.execute(incoming_query, incoming_params)
            incoming_rows = cursor.fetchall()

            conn.close()

            # Process results
            related_memories = []
            for row in outgoing_rows + incoming_rows:
                # The last three columns are relationship_type, strength, and direction
                memory_data = {
                    "memory": cls(
                        memory_id=row[0],
                        user_id=row[1],
                        content=row[2],
                        category=row[3],
                        importance=row[4],
                        source=row[5],
                        context=row[6],
                        last_accessed=row[7],
                        created_at=row[8],
                        confidence=row[9],
                        expires_at=row[10],
                        recall_count=row[11],
                        last_reinforced=row[12],
                        is_consolidated=bool(row[13])
                    ).to_dict(),
                    "relationship": {
                        "type": row[-3],
                        "strength": row[-2],
                        "direction": row[-1]
                    }
                }
                related_memories.append(memory_data)

            return related_memories

        except Exception as e:
            logger.error(f"Error getting related memories: {str(e)}")
            return []

    @classmethod
    async def consolidate_memories(cls, user_id: int, memory_ids: List[int],
                                   consolidated_content: str, category: str = "consolidated",
                                   importance: int = 3, confidence: float = 0.8) -> Optional[int]:
        """
        Consolidate multiple memories into a single higher-level memory.

        Args:
            user_id (int): User ID
            memory_ids (List[int]): List of memory IDs to consolidate
            consolidated_content (str): Content of the consolidated memory
            category (str): Category for the consolidated memory
            importance (int): Importance level for the consolidated memory (1-5)
            confidence (float): Confidence level for the consolidated memory (0.0-1.0)

        Returns:
            Optional[int]: ID of the consolidated memory if successful, None otherwise
        """
        try:
            # Get the source memories to ensure they exist and belong to the user
            source_memories = []
            for memory_id in memory_ids:
                memories = await cls.get_memories(user_id=user_id, limit=1)
                if memories and memories[0].memory_id == memory_id:
                    source_memories.append(memories[0])

            if len(source_memories) != len(memory_ids):
                logger.warning(
                    f"Not all memories found for consolidation for user {user_id}")
                return None

            # Create the consolidated memory
            context = f"Consolidated from {len(memory_ids)} memories: {', '.join([str(mid) for mid in memory_ids])}"

            # Extract tags from source memories
            all_tags = set()
            for memory in source_memories:
                if memory.tags:
                    all_tags.update(memory.tags)

            # Create the consolidated memory
            consolidated_memory_id = await cls.add_memory(
                user_id=user_id,
                content=consolidated_content,
                category=category,
                importance=importance,
                source="consolidated",
                context=context,
                confidence=confidence,
                tags=list(all_tags),
                is_consolidated=True
            )

            if not consolidated_memory_id:
                logger.error(
                    f"Failed to create consolidated memory for user {user_id}")
                return None

            # Create relationships between source memories and the consolidated memory
            for memory in source_memories:
                await cls.add_memory_relationship(
                    source_memory_id=memory.memory_id,
                    target_memory_id=consolidated_memory_id,
                    relationship_type="part_of",
                    strength=0.9
                )

            # Log the consolidation
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """INSERT INTO memory_consolidation_log
                   (user_id, source_memories, consolidated_memory_id, consolidation_type)
                   VALUES (?, ?, ?, ?)""",
                (user_id, json.dumps(memory_ids), consolidated_memory_id, "manual")
            )

            conn.commit()
            conn.close()

            return consolidated_memory_id

        except Exception as e:
            logger.error(
                f"Error consolidating memories for user {user_id}: {str(e)}")
            return None
