"""
Memory management module for Jyra.

This module coordinates memory operations including extraction, retrieval, and consolidation.
"""

from typing import List, Dict, Any, Optional
from jyra.ai.memory_consolidator import memory_consolidator
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryManager:
    """
    Class for managing all memory operations.
    """

    def __init__(self):
        """Initialize the memory manager."""
        # We'll use the existing memory components
        pass

    async def process_user_message(self, user_id: int, message: str,
                                   user_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Process a user message to extract and store memories.

        Args:
            user_id (int): User ID
            message (str): User message
            user_context (Optional[Dict[str, Any]]): Additional context about the user

        Returns:
            List[Dict[str, Any]]: List of extracted memories
        """
        try:
            # Extract memories from the message
            extracted_memories = await Memory.extract_memories_from_message(
                user_id=user_id,
                text=message,
                context=user_context
            )

            logger.info(
                f"Extracted {len(extracted_memories)} memories from message for user {user_id}")

            return extracted_memories

        except Exception as e:
            logger.error(
                f"Error processing user message for memory extraction: {str(e)}")
            return []

    async def get_relevant_memories(self, user_id: int, context: str,
                                    max_memories: int = 5,
                                    min_importance: int = 2,
                                    use_semantic: bool = True,
                                    recency_weight: float = 0.3) -> List[Dict[str, Any]]:
        """
        Get memories relevant to the current context with improved prioritization.

        This method uses a combination of semantic relevance, importance, and recency
        to retrieve the most relevant memories for the current context.

        Args:
            user_id (int): User ID
            context (str): Current conversation context
            max_memories (int): Maximum number of memories to retrieve
            min_importance (int): Minimum importance level
            use_semantic (bool): Whether to use semantic search
            recency_weight (float): Weight to give to recency in scoring (0-1)

        Returns:
            List[Dict[str, Any]]: List of relevant memories sorted by relevance score
        """
        try:
            # Get a larger set of memories to apply our custom ranking
            # Get more memories than needed for better ranking
            search_limit = max(max_memories * 3, 15)

            if use_semantic and context.strip():
                # Use semantic search to find relevant memories
                memories = await Memory.search_memories(
                    user_id=user_id,
                    query=context,
                    limit=search_limit,
                    use_semantic=True
                )

                # Filter by importance
                memories = [
                    m for m in memories if m.importance >= min_importance]
            else:
                # Fall back to importance-based retrieval
                memories = await Memory.get_memories(
                    user_id=user_id,
                    min_importance=min_importance,
                    limit=search_limit,
                    sort_by="last_accessed"
                )

            if not memories:
                return []

            # Calculate a relevance score for each memory
            # Score = (semantic_score * (1 - recency_weight)) + (recency_score * recency_weight)
            scored_memories = []

            # Get the most recent timestamp for normalization
            most_recent = max(
                m.last_accessed for m in memories if m.last_accessed)
            oldest = min(m.last_accessed for m in memories if m.last_accessed)
            # Avoid division by zero
            time_range = max((most_recent - oldest).total_seconds(), 1)

            # Get the highest importance for normalization
            max_importance = max(m.importance for m in memories)

            for memory in memories:
                # Calculate normalized recency score (0-1)
                if memory.last_accessed:
                    recency_score = (memory.last_accessed -
                                     oldest).total_seconds() / time_range
                else:
                    recency_score = 0

                # Calculate normalized importance score (0-1)
                importance_score = memory.importance / max_importance

                # Calculate semantic score (already normalized by the search function)
                # Default to 0.5 if not available
                semantic_score = getattr(memory, 'semantic_score', 0.5)

                # Calculate final score with weights
                # 50% semantic, 30% importance, 20% recency (adjustable)
                final_score = (
                    semantic_score * 0.5 +
                    importance_score * 0.3 +
                    recency_score * 0.2
                )

                scored_memories.append((memory, final_score))

            # Sort by score (descending) and take top memories
            scored_memories.sort(key=lambda x: x[1], reverse=True)
            top_memories = [memory for memory,
                            _ in scored_memories[:max_memories]]

            # Update last_accessed for these memories
            memory_ids = [memory.memory_id for memory in top_memories]
            await Memory.update_last_accessed(memory_ids)

            logger.info(
                f"Retrieved {len(top_memories)} relevant memories for user {user_id}")
            return [memory.to_dict() for memory in top_memories]

        except Exception as e:
            logger.error(f"Error getting relevant memories: {str(e)}")
            return []

    async def get_memory_by_tags(self, user_id: int, tags: List[str],
                                 max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories by tags.

        Args:
            user_id (int): User ID
            tags (List[str]): List of tags to search for
            max_memories (int): Maximum number of memories to retrieve

        Returns:
            List[Dict[str, Any]]: List of memories with the specified tags
        """
        try:
            memories = await Memory.get_memories(
                user_id=user_id,
                tags=tags,
                limit=max_memories
            )

            return [memory.to_dict() for memory in memories]

        except Exception as e:
            logger.error(f"Error getting memories by tags: {str(e)}")
            return []

    async def get_memory_by_category(self, user_id: int, category: str,
                                     max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories by category.

        Args:
            user_id (int): User ID
            category (str): Category to search for
            max_memories (int): Maximum number of memories to retrieve

        Returns:
            List[Dict[str, Any]]: List of memories in the specified category
        """
        try:
            memories = await Memory.get_memories(
                user_id=user_id,
                category=category,
                limit=max_memories
            )

            return [memory.to_dict() for memory in memories]

        except Exception as e:
            logger.error(f"Error getting memories by category: {str(e)}")
            return []

    async def search_memories(self, user_id: int, query: str,
                              limit: int = 10, use_semantic: bool = True) -> List[Dict[str, Any]]:
        """
        Search memories by content using keyword or semantic search.

        Args:
            user_id (int): User ID
            query (str): Search query
            limit (int): Maximum number of memories to retrieve
            use_semantic (bool): Whether to use semantic search

        Returns:
            List[Dict[str, Any]]: List of matching memories
        """
        try:
            memories = await Memory.search_memories(
                user_id=user_id,
                query=query,
                limit=limit,
                use_semantic=use_semantic
            )

            return [memory.to_dict() for memory in memories]

        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return []

    async def run_memory_maintenance(self, user_id: int) -> Dict[str, Any]:
        """
        Run memory maintenance tasks including consolidation.

        Args:
            user_id (int): User ID

        Returns:
            Dict[str, Any]: Results of maintenance operations
        """
        try:
            results = {
                "consolidated_memories": 0,
                "expired_memories": 0,
                "updated_memories": 0
            }

            # Run consolidation cycle
            consolidated_memory_ids = await memory_consolidator.run_consolidation_cycle(user_id)
            results["consolidated_memories"] = len(consolidated_memory_ids)

            # Clean up expired memories
            # This would be implemented in a more advanced version

            logger.info(
                f"Memory maintenance completed for user {user_id}: {results}")

            return results

        except Exception as e:
            logger.error(f"Error running memory maintenance: {str(e)}")
            return {"error": str(e)}

    async def update_memory_importance(self, memory_id: int, importance_change: int = 1) -> bool:
        """
        Update the importance of a memory based on its usage.

        This method increases or decreases the importance of a memory,
        which affects how likely it is to be retrieved in the future.

        Args:
            memory_id (int): The ID of the memory to update
            importance_change (int): The amount to change the importance by (positive or negative)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the current memory
            memory = await Memory.get_memory(memory_id)
            if not memory:
                logger.warning(
                    f"Cannot update importance: Memory {memory_id} not found")
                return False

            # Calculate new importance (clamped between 1-10)
            new_importance = max(
                1, min(10, memory.importance + importance_change))

            # Update the memory if importance changed
            if new_importance != memory.importance:
                success = await Memory.update_memory(
                    memory_id=memory_id,
                    updates={"importance": new_importance}
                )
                if success:
                    logger.info(
                        f"Updated memory {memory_id} importance from {memory.importance} to {new_importance}")
                return success
            return True

        except Exception as e:
            logger.error(f"Error updating memory importance: {str(e)}")
            return False

    async def format_memories_for_context(self, memories: List[Dict[str, Any]],
                                          max_length: int = 1000) -> str:
        """
        Format memories for inclusion in conversation context.

        Args:
            memories (List[Dict[str, Any]]): List of memories
            max_length (int): Maximum length of the formatted context

        Returns:
            str: Formatted memory context
        """
        try:
            if not memories:
                return ""

            # Sort memories by importance
            sorted_memories = sorted(
                memories, key=lambda m: m.get("importance", 0), reverse=True)

            # Format each memory
            formatted_memories = []
            for memory in sorted_memories:
                category = memory.get("category", "general").capitalize()
                content = memory.get("content", "")
                importance = memory.get("importance", 1)
                # Add importance indicator for debugging (can be removed in production)
                formatted = f"{category} [I:{importance}]: {content}"
                formatted_memories.append(formatted)

            # Join and truncate if necessary
            context = "User Memory Context:\n" + "\n".join(formatted_memories)

            if len(context) > max_length:
                context = context[:max_length-3] + "..."

            return context

        except Exception as e:
            logger.error(f"Error formatting memories for context: {str(e)}")
            return ""


# Create a singleton instance
memory_manager = MemoryManager()
