"""
Memory consolidation module for Jyra.

This module provides functionality to consolidate related memories using semantic clustering.
"""

import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
import json
from sklearn.cluster import DBSCAN, AgglomerativeClustering
import networkx as nx

from jyra.db.models.memory import Memory
from jyra.ai.embeddings.vector_db import vector_db
from jyra.ai.models.model_manager import model_manager
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryConsolidator:
    """
    Class for consolidating related memories using semantic clustering.
    """

    def __init__(self):
        """
        Initialize the memory consolidator.
        """
        logger.info("Initializing memory consolidator")

    async def identify_consolidation_candidates(self,
                                                user_id: int,
                                                min_similarity: float = 0.75,
                                                max_memories: int = 100,
                                                min_importance: int = 1,
                                                min_cluster_size: int = 2,
                                                max_cluster_size: int = 5) -> List[List[Memory]]:
        """
        Identify groups of memories that are candidates for consolidation.

        Args:
            user_id (int): User ID
            min_similarity (float): Minimum similarity threshold for clustering
            max_memories (int): Maximum number of memories to analyze
            min_importance (int): Minimum importance level for memories
            min_cluster_size (int): Minimum size of clusters to consider
            max_cluster_size (int): Maximum size of clusters to consider

        Returns:
            List[List[Memory]]: List of memory clusters that are candidates for consolidation
        """
        try:
            # Get memories for the user
            memories = await Memory.get_memories(
                user_id=user_id,
                min_importance=min_importance,
                limit=max_memories,
                sort_by="last_accessed"  # Focus on recently accessed memories
            )

            if not memories or len(memories) < min_cluster_size:
                logger.info(
                    f"Not enough memories for user {user_id} to identify consolidation candidates")
                return []

            # Get embeddings for all memories
            memory_embeddings = {}
            for memory in memories:
                embedding = await vector_db.get_embedding(memory.memory_id)
                if embedding:
                    memory_embeddings[memory.memory_id] = embedding

            if len(memory_embeddings) < min_cluster_size:
                logger.info(
                    f"Not enough embeddings for user {user_id} to identify consolidation candidates")
                return []

            # Create a similarity matrix
            memory_ids = list(memory_embeddings.keys())
            n_memories = len(memory_ids)
            similarity_matrix = np.zeros((n_memories, n_memories))

            for i in range(n_memories):
                for j in range(i, n_memories):
                    if i == j:
                        similarity_matrix[i, j] = 1.0
                    else:
                        similarity = vector_db.calculate_similarity(
                            memory_embeddings[memory_ids[i]],
                            memory_embeddings[memory_ids[j]]
                        )
                        similarity_matrix[i, j] = similarity
                        similarity_matrix[j, i] = similarity

            # Convert similarity matrix to distance matrix (1 - similarity)
            distance_matrix = 1 - similarity_matrix

            # Use DBSCAN for clustering
            clustering = DBSCAN(
                eps=1 - min_similarity,  # Convert similarity threshold to distance threshold
                min_samples=min_cluster_size - 1,  # min_samples is one less than min_cluster_size
                metric='precomputed'
            ).fit(distance_matrix)

            # Get cluster labels
            labels = clustering.labels_

            # Group memories by cluster
            clusters = {}
            for i, label in enumerate(labels):
                if label != -1:  # Ignore noise points
                    if label not in clusters:
                        clusters[label] = []
                    memory_id = memory_ids[i]
                    # Find the memory object
                    for memory in memories:
                        if memory.memory_id == memory_id:
                            clusters[label].append(memory)
                            break

            # Filter clusters by size
            valid_clusters = []
            for cluster in clusters.values():
                if min_cluster_size <= len(cluster) <= max_cluster_size:
                    valid_clusters.append(cluster)

            # Sort clusters by average similarity
            sorted_clusters = self._sort_clusters_by_coherence(
                valid_clusters, similarity_matrix, memory_ids)

            return sorted_clusters

        except Exception as e:
            logger.error(
                f"Error identifying consolidation candidates: {str(e)}")
            return []

    def _sort_clusters_by_coherence(self,
                                    clusters: List[List[Memory]],
                                    similarity_matrix: np.ndarray,
                                    memory_ids: List[int]) -> List[List[Memory]]:
        """
        Sort clusters by their coherence (average similarity).

        Args:
            clusters (List[List[Memory]]): List of memory clusters
            similarity_matrix (np.ndarray): Similarity matrix
            memory_ids (List[int]): List of memory IDs

        Returns:
            List[List[Memory]]: Sorted list of memory clusters
        """
        try:
            cluster_scores = []

            for cluster in clusters:
                # Get indices of memories in this cluster
                cluster_memory_ids = [memory.memory_id for memory in cluster]
                indices = [memory_ids.index(
                    mid) for mid in cluster_memory_ids if mid in memory_ids]

                # Calculate average similarity within cluster
                if len(indices) < 2:
                    avg_similarity = 0
                else:
                    similarities = []
                    for i in range(len(indices)):
                        for j in range(i+1, len(indices)):
                            similarities.append(
                                similarity_matrix[indices[i], indices[j]])
                    avg_similarity = sum(similarities) / \
                        len(similarities) if similarities else 0

                cluster_scores.append((cluster, avg_similarity))

            # Sort by average similarity (descending)
            cluster_scores.sort(key=lambda x: x[1], reverse=True)

            return [cluster for cluster, _ in cluster_scores]

        except Exception as e:
            logger.error(f"Error sorting clusters: {str(e)}")
            return clusters

    async def generate_consolidated_memory(self,
                                           memories: List[Memory],
                                           user_id: int) -> Optional[Dict[str, Any]]:
        """
        Generate a consolidated memory from a list of related memories.

        Args:
            memories (List[Memory]): List of memories to consolidate
            user_id (int): User ID

        Returns:
            Optional[Dict[str, Any]]: Consolidated memory data, or None if consolidation failed
        """
        try:
            if not memories or len(memories) < 2:
                logger.warning("Not enough memories to consolidate")
                return None

            # Extract memory contents and metadata
            memory_contents = [memory.content for memory in memories]
            categories = set(
                memory.category for memory in memories if memory.category)
            all_tags = set()
            for memory in memories:
                if memory.tags:
                    all_tags.update(memory.tags)

            # Calculate average importance
            avg_importance = sum(
                memory.importance for memory in memories) / len(memories)
            importance = min(5, max(1, round(avg_importance)))

            # Prepare prompt for the AI model
            prompt = f"""You are an AI assistant helping to consolidate related memories into a single, comprehensive memory.
Please analyze these related memories and create a single consolidated memory that captures all the important information.

MEMORIES TO CONSOLIDATE:
{chr(10).join([f"- {content}" for content in memory_contents])}

GUIDELINES:
1. Combine all important information from the memories
2. Remove redundancies and duplications
3. Organize the information in a logical way
4. Keep the consolidated memory concise but comprehensive
5. Use clear, factual language
6. Preserve specific details, names, dates, and numbers

Please provide ONLY the consolidated memory text, without any explanations or additional comments."""

            # Generate consolidated memory content
            response_tuple = await model_manager.generate_response(prompt, user_id=user_id)

            if not response_tuple or not response_tuple[0]:
                logger.error("Failed to generate consolidated memory content")
                return None

            # Extract the response text from the tuple (response, model_name)
            response_text = response_tuple[0]
            consolidated_content = response_text.strip()

            # Determine the best category
            category = self._determine_best_category(categories)

            # Create consolidated memory data
            consolidated_memory = {
                "content": consolidated_content,
                "category": category,
                "importance": importance,
                "tags": list(all_tags),
                "source": "consolidation",
                "context": f"Consolidated from {len(memories)} related memories",
                "is_consolidated": True,
                "original_memory_ids": [memory.memory_id for memory in memories]
            }

            return consolidated_memory

        except Exception as e:
            logger.error(f"Error generating consolidated memory: {str(e)}")
            return None

    def _determine_best_category(self, categories: Set[str]) -> str:
        """
        Determine the best category for a consolidated memory.

        Args:
            categories (Set[str]): Set of categories from original memories

        Returns:
            str: Best category
        """
        if not categories:
            return "General"

        # If there's only one category, use it
        if len(categories) == 1:
            return next(iter(categories))

        # Count category frequencies
        category_counts = {}
        for category in categories:
            if category in category_counts:
                category_counts[category] += 1
            else:
                category_counts[category] = 1

        # Return the most frequent category
        return max(category_counts.items(), key=lambda x: x[1])[0]

    async def perform_consolidation(self,
                                    user_id: int,
                                    memories: List[Memory],
                                    mark_originals: bool = True) -> Optional[int]:
        """
        Perform consolidation of a group of memories.

        Args:
            user_id (int): User ID
            memories (List[Memory]): List of memories to consolidate
            mark_originals (bool): Whether to mark original memories as consolidated

        Returns:
            Optional[int]: ID of the new consolidated memory, or None if consolidation failed
        """
        try:
            # Generate consolidated memory
            consolidated_data = await self.generate_consolidated_memory(memories, user_id)

            if not consolidated_data:
                logger.error("Failed to generate consolidated memory")
                return None

            # Create new memory
            new_memory = Memory(
                user_id=user_id,
                content=consolidated_data["content"],
                category=consolidated_data["category"],
                importance=consolidated_data["importance"],
                source=consolidated_data["source"],
                context=consolidated_data["context"],
                is_consolidated=True,
                tags=consolidated_data["tags"]
            )

            # Save the new memory
            new_memory_id = await new_memory.save()

            if not new_memory_id:
                logger.error("Failed to save consolidated memory")
                return None

            # Mark original memories as consolidated if requested
            if mark_originals:
                for memory in memories:
                    await Memory.mark_as_consolidated(memory.memory_id, new_memory_id)

            logger.info(
                f"Successfully consolidated {len(memories)} memories into new memory {new_memory_id}")
            return new_memory_id

        except Exception as e:
            logger.error(f"Error performing consolidation: {str(e)}")
            return None

    async def run_auto_consolidation(self,
                                     user_id: int,
                                     min_similarity: float = 0.75,
                                     max_consolidations: int = 3) -> Dict[str, Any]:
        """
        Run automatic consolidation for a user.

        Args:
            user_id (int): User ID
            min_similarity (float): Minimum similarity threshold for clustering
            max_consolidations (int): Maximum number of consolidations to perform

        Returns:
            Dict[str, Any]: Results of the consolidation process
        """
        try:
            # Identify consolidation candidates
            candidates = await self.identify_consolidation_candidates(
                user_id=user_id,
                min_similarity=min_similarity
            )

            if not candidates:
                logger.info(
                    f"No consolidation candidates found for user {user_id}")
                return {
                    "success": True,
                    "consolidated_count": 0,
                    "message": "No memories suitable for consolidation were found."
                }

            # Limit the number of consolidations
            candidates = candidates[:max_consolidations]

            # Perform consolidations
            consolidated_count = 0
            consolidated_memory_ids = []

            for cluster in candidates:
                new_memory_id = await self.perform_consolidation(user_id, cluster)
                if new_memory_id:
                    consolidated_count += 1
                    consolidated_memory_ids.append(new_memory_id)

            return {
                "success": True,
                "consolidated_count": consolidated_count,
                "consolidated_memory_ids": consolidated_memory_ids,
                "message": f"Successfully consolidated {consolidated_count} groups of memories."
            }

        except Exception as e:
            logger.error(f"Error running auto consolidation: {str(e)}")
            return {
                "success": False,
                "consolidated_count": 0,
                "message": f"Error running auto consolidation: {str(e)}"
            }


# Create a singleton instance
memory_consolidator = MemoryConsolidator()
