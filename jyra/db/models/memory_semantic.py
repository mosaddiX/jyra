"""
Semantic search extensions for the Memory model.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger
from jyra.ai.embeddings.embedding_generator import embedding_generator
from jyra.ai.embeddings.vector_db import vector_db

logger = setup_logger(__name__)


async def semantic_search(user_id: int, query: str, limit: Optional[int] = None,
                          min_similarity: float = 0.7) -> List[Dict[str, Any]]:
    """
    Search for memories by content using semantic search.

    Args:
        user_id (int): User ID
        query (str): Search query
        limit (Optional[int]): Maximum number of memories to retrieve
        min_similarity (float): Minimum similarity score (0-1)

    Returns:
        List[Dict[str, Any]]: List of matching memories with similarity scores
    """
    try:
        # Try to generate embedding for the query using Gemini
        try:
            query_embedding = await embedding_generator.generate_embedding(query)
        except Exception as e:
            logger.warning(
                f"Error with Gemini embedding, trying OpenAI fallback: {str(e)}")
            # Try OpenAI as fallback
            from jyra.ai.embeddings.embedding_generator import EmbeddingGenerator
            openai_generator = EmbeddingGenerator(
                model_name="text-embedding-3-small")
            query_embedding = await openai_generator.generate_embedding(query)

        # Search for similar embeddings
        similar_memories = await vector_db.search_similar(
            query_embedding=query_embedding,
            limit=limit or 10,
            min_similarity=min_similarity
        )

        if not similar_memories:
            logger.info(f"No similar memories found for query: {query}")
            return []

        # Get memory details for the similar memories
        memory_ids = [memory_id for memory_id, _ in similar_memories]
        memories_with_similarity = []

        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        for memory_id, similarity in similar_memories:
            # Get the memory details
            cursor.execute(
                """SELECT m.memory_id, m.user_id, m.content, m.category, m.importance,
                          m.source, m.context, m.last_accessed, m.created_at, m.confidence,
                          m.expires_at, m.recall_count, m.last_reinforced, m.is_consolidated
                   FROM memories m
                   WHERE m.memory_id = ? AND m.user_id = ?""",
                (memory_id, user_id)
            )

            row = cursor.fetchone()
            if row:
                # Get tags for this memory
                cursor.execute(
                    """SELECT mt.tag_name
                       FROM memory_tag_associations mta
                       JOIN memory_tags mt ON mta.tag_id = mt.tag_id
                       WHERE mta.memory_id = ?""",
                    (memory_id,)
                )

                tags = [tag[0] for tag in cursor.fetchall()]

                # Create memory dict with similarity score
                memory_dict = {
                    "memory_id": row[0],
                    "user_id": row[1],
                    "content": row[2],
                    "category": row[3],
                    "importance": row[4],
                    "source": row[5],
                    "context": row[6],
                    "last_accessed": row[7],
                    "created_at": row[8],
                    "confidence": row[9],
                    "expires_at": row[10],
                    "recall_count": row[11],
                    "last_reinforced": row[12],
                    "is_consolidated": bool(row[13]),
                    "tags": tags,
                    "similarity": similarity
                }

                memories_with_similarity.append(memory_dict)

        conn.close()

        # Update last_accessed for retrieved memories
        from jyra.db.models.memory import Memory
        await Memory._update_last_accessed(memory_ids)

        return memories_with_similarity

    except Exception as e:
        logger.error(
            f"Error semantic searching memories for user {user_id}: {str(e)}")
        return []


async def get_memory_by_id(user_id: int, memory_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a memory by ID.

    Args:
        user_id (int): User ID for permission check
        memory_id (int): Memory ID to retrieve

    Returns:
        Optional[Dict[str, Any]]: Memory data if found, None otherwise
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(
            """SELECT m.memory_id, m.user_id, m.content, m.category, m.importance,
                      m.source, m.context, m.last_accessed, m.created_at, m.confidence,
                      m.expires_at, m.recall_count, m.last_reinforced, m.is_consolidated
               FROM memories m
               WHERE m.memory_id = ? AND m.user_id = ?""",
            (memory_id, user_id)
        )

        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Get tags for this memory
        cursor.execute(
            """SELECT mt.tag_name
               FROM memory_tag_associations mta
               JOIN memory_tags mt ON mta.tag_id = mt.tag_id
               WHERE mta.memory_id = ?""",
            (memory_id,)
        )

        tags = [tag[0] for tag in cursor.fetchall()]

        conn.close()

        # Create memory dict
        memory_dict = {
            "memory_id": row[0],
            "user_id": row[1],
            "content": row[2],
            "category": row[3],
            "importance": row[4],
            "source": row[5],
            "context": row[6],
            "last_accessed": row[7],
            "created_at": row[8],
            "confidence": row[9],
            "expires_at": row[10],
            "recall_count": row[11],
            "last_reinforced": row[12],
            "is_consolidated": bool(row[13]),
            "tags": tags
        }

        # Update last_accessed
        from jyra.db.models.memory import Memory
        await Memory._update_last_accessed([memory_id])

        return memory_dict

    except Exception as e:
        logger.error(
            f"Error getting memory by ID {memory_id} for user {user_id}: {str(e)}")
        return None


async def generate_embeddings_for_all_memories():
    """
    Generate embeddings for all memories that don't have them yet.

    This is useful for initializing the vector database with existing memories.
    """
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Get all memories that don't have embeddings
        cursor.execute(
            """SELECT m.memory_id, m.content
               FROM memories m
               LEFT JOIN memory_embeddings me ON m.memory_id = me.memory_id
               WHERE me.memory_id IS NULL"""
        )

        rows = cursor.fetchall()
        conn.close()

        if not rows:
            logger.info("No memories found without embeddings")
            return

        logger.info(f"Generating embeddings for {len(rows)} memories")

        # Generate embeddings in batches
        batch_size = 10
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]

            for memory_id, content in batch:
                try:
                    # Try to generate embedding using Gemini
                    try:
                        embedding = await embedding_generator.generate_embedding(content)
                    except Exception as e:
                        logger.warning(
                            f"Error with Gemini embedding for memory {memory_id}, trying OpenAI fallback: {str(e)}")
                        # Try OpenAI as fallback
                        from jyra.ai.embeddings.embedding_generator import EmbeddingGenerator
                        openai_generator = EmbeddingGenerator(
                            model_name="text-embedding-3-small")
                        embedding = await openai_generator.generate_embedding(content)

                    # Store embedding
                    await vector_db.store_embedding(memory_id, embedding)

                    logger.info(f"Generated embedding for memory {memory_id}")
                except Exception as e:
                    logger.error(
                        f"Error generating embedding for memory {memory_id}: {str(e)}")

        logger.info("Finished generating embeddings for all memories")

    except Exception as e:
        logger.error(f"Error generating embeddings for all memories: {str(e)}")


async def update_memory_embedding(memory_id: int, content: str) -> bool:
    """
    Update the embedding for a memory.

    Args:
        memory_id (int): Memory ID
        content (str): Memory content to generate embedding from

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Try to generate embedding using Gemini
        try:
            embedding = await embedding_generator.generate_embedding(content)
        except Exception as e:
            logger.warning(
                f"Error with Gemini embedding for memory {memory_id}, trying OpenAI fallback: {str(e)}")
            # Try OpenAI as fallback
            from jyra.ai.embeddings.embedding_generator import EmbeddingGenerator
            openai_generator = EmbeddingGenerator(
                model_name="text-embedding-3-small")
            embedding = await openai_generator.generate_embedding(content)

        # Store embedding
        success = await vector_db.store_embedding(memory_id, embedding)

        return success

    except Exception as e:
        logger.error(
            f"Error updating embedding for memory {memory_id}: {str(e)}")
        return False
