"""
Vector database for Jyra.

This module provides a simple vector database for storing and retrieving embeddings.
"""

import sqlite3
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
import os
from pathlib import Path

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger
from jyra.ai.embeddings.embedding_generator import embedding_generator

logger = setup_logger(__name__)


class VectorDatabase:
    """
    Class for storing and retrieving vector embeddings.
    """

    def __init__(self, db_path: str = DATABASE_PATH):
        """
        Initialize the vector database.

        Args:
            db_path (str): Path to the SQLite database
        """
        self.db_path = db_path
        self._ensure_tables_exist()
        logger.info("Initialized vector database")

    def _ensure_tables_exist(self) -> None:
        """
        Ensure the necessary tables exist in the database.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create memory_embeddings table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_embeddings (
                memory_id INTEGER PRIMARY KEY,
                embedding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories (memory_id) ON DELETE CASCADE
            )
            ''')

            # Create index on memory_id
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memory_embeddings_memory_id ON memory_embeddings (memory_id)
            ''')

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"Error ensuring tables exist: {str(e)}")

    async def store_embedding(self, memory_id: int, embedding: List[float]) -> bool:
        """
        Store a vector embedding for a memory.

        Args:
            memory_id (int): The ID of the memory
            embedding (List[float]): The vector embedding

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Convert embedding to bytes
            embedding_bytes = self._serialize_embedding(embedding)

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check if embedding already exists
            cursor.execute(
                "SELECT memory_id FROM memory_embeddings WHERE memory_id = ?",
                (memory_id,)
            )

            existing_embedding = cursor.fetchone()

            if existing_embedding:
                # Update existing embedding
                cursor.execute(
                    "UPDATE memory_embeddings SET embedding = ?, updated_at = CURRENT_TIMESTAMP WHERE memory_id = ?",
                    (embedding_bytes, memory_id)
                )
                logger.info(f"Updated embedding for memory {memory_id}")
            else:
                # Insert new embedding
                cursor.execute(
                    "INSERT INTO memory_embeddings (memory_id, embedding) VALUES (?, ?)",
                    (memory_id, embedding_bytes)
                )
                logger.info(f"Stored embedding for memory {memory_id}")

            conn.commit()
            conn.close()

            return True

        except Exception as e:
            logger.error(
                f"Error storing embedding for memory {memory_id}: {str(e)}")
            return False

    async def get_embedding(self, memory_id: int) -> Optional[List[float]]:
        """
        Get the vector embedding for a memory.

        Args:
            memory_id (int): The ID of the memory

        Returns:
            Optional[List[float]]: The vector embedding, or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT embedding FROM memory_embeddings WHERE memory_id = ?",
                (memory_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                # Deserialize embedding
                embedding = self._deserialize_embedding(row[0])
                return embedding

            return None

        except Exception as e:
            logger.error(
                f"Error getting embedding for memory {memory_id}: {str(e)}")
            return None

    async def search_similar(self, query_embedding: List[float], limit: int = 10, min_similarity: float = 0.7) -> List[Tuple[int, float]]:
        """
        Search for memories with similar embeddings.

        Args:
            query_embedding (List[float]): The query embedding
            limit (int): Maximum number of results to return
            min_similarity (float): Minimum similarity score (0-1)

        Returns:
            List[Tuple[int, float]]: List of (memory_id, similarity_score) tuples
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get all embeddings
            cursor.execute(
                "SELECT memory_id, embedding FROM memory_embeddings")
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return []

            # Calculate similarity scores
            results = []
            for memory_id, embedding_bytes in rows:
                embedding = self._deserialize_embedding(embedding_bytes)
                similarity = embedding_generator.cosine_similarity(
                    query_embedding, embedding)

                if similarity >= min_similarity:
                    results.append((memory_id, similarity))

            # Sort by similarity (highest first)
            results.sort(key=lambda x: x[1], reverse=True)

            # Limit results
            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching similar embeddings: {str(e)}")
            return []

    async def delete_embedding(self, memory_id: int) -> bool:
        """
        Delete the vector embedding for a memory.

        Args:
            memory_id (int): The ID of the memory

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM memory_embeddings WHERE memory_id = ?",
                (memory_id,)
            )

            conn.commit()
            conn.close()

            logger.info(f"Deleted embedding for memory {memory_id}")
            return True

        except Exception as e:
            logger.error(
                f"Error deleting embedding for memory {memory_id}: {str(e)}")
            return False

    def _serialize_embedding(self, embedding: Union[List[float], Dict[str, Any]]) -> bytes:
        """
        Serialize a vector embedding to bytes.

        Args:
            embedding (Union[List[float], Dict[str, Any]]): The vector embedding

        Returns:
            bytes: The serialized embedding
        """
        # Handle different embedding formats
        if isinstance(embedding, dict):
            # Extract values from the embedding dictionary
            if 'values' in embedding:
                # Gemini format
                values = embedding['values']
            else:
                # Try to convert the entire dict to a list
                values = list(embedding.values())
        else:
            # Already a list
            values = embedding

        # Convert to numpy array and then to bytes
        return np.array(values, dtype=np.float32).tobytes()

    def _deserialize_embedding(self, embedding_bytes: bytes) -> List[float]:
        """
        Deserialize a vector embedding from bytes.

        Args:
            embedding_bytes (bytes): The serialized embedding

        Returns:
            List[float]: The vector embedding
        """
        # Convert from bytes to numpy array and then to list
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
        return embedding

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate the cosine similarity between two embeddings.

        Args:
            embedding1 (List[float]): First embedding
            embedding2 (List[float]): Second embedding

        Returns:
            float: Similarity score between 0 and 1
        """
        try:
            return embedding_generator.cosine_similarity(embedding1, embedding2)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            # Fallback to manual calculation
            try:
                # Convert to numpy arrays
                vec1 = np.array(embedding1)
                vec2 = np.array(embedding2)

                # Calculate cosine similarity
                dot_product = np.dot(vec1, vec2)
                norm1 = np.linalg.norm(vec1)
                norm2 = np.linalg.norm(vec2)

                if norm1 == 0 or norm2 == 0:
                    return 0.0

                return dot_product / (norm1 * norm2)
            except Exception as e2:
                logger.error(
                    f"Fallback similarity calculation failed: {str(e2)}")
                return 0.0


# Create a singleton instance
vector_db = VectorDatabase()
