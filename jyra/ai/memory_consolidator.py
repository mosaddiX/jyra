"""
Memory consolidation module for Jyra.

This module consolidates related memories to create higher-level memories.
"""

import json
from typing import List, Dict, Any, Optional, Set

from jyra.ai.models.model_manager import model_manager
from jyra.db.models.memory import Memory
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryConsolidator:
    """
    Class for consolidating related memories into higher-level memories.
    """

    def __init__(self):
        """Initialize the memory consolidator."""
        # We'll use the model_manager for AI-powered consolidation
        pass

    async def find_consolidation_candidates(self, user_id: int, 
                                           min_memories: int = 3, 
                                           max_memories: int = 10,
                                           category: Optional[str] = None,
                                           min_importance: int = 1) -> List[List[Dict[str, Any]]]:
        """
        Find groups of memories that are candidates for consolidation.

        Args:
            user_id (int): User ID
            min_memories (int): Minimum number of memories in a group
            max_memories (int): Maximum number of memories in a group
            category (Optional[str]): Filter by category
            min_importance (int): Minimum importance level

        Returns:
            List[List[Dict[str, Any]]]: List of memory groups for consolidation
        """
        try:
            # Get all memories for the user
            memories = await Memory.get_memories(
                user_id=user_id,
                category=category,
                min_importance=min_importance,
                include_expired=False
            )
            
            if len(memories) < min_memories:
                logger.info(f"Not enough memories for consolidation for user {user_id}")
                return []
                
            # Group memories by category
            category_groups = {}
            for memory in memories:
                if memory.is_consolidated:
                    continue  # Skip already consolidated memories
                    
                if memory.category not in category_groups:
                    category_groups[memory.category] = []
                category_groups[memory.category].append(memory.to_dict())
                
            # Find groups with enough memories for consolidation
            consolidation_candidates = []
            for category, memory_group in category_groups.items():
                if len(memory_group) >= min_memories:
                    # For now, just group by category
                    # In a more advanced implementation, we could use clustering or similarity
                    if len(memory_group) <= max_memories:
                        consolidation_candidates.append(memory_group)
                    else:
                        # Split into smaller groups if too many memories
                        for i in range(0, len(memory_group), max_memories):
                            group = memory_group[i:i+max_memories]
                            if len(group) >= min_memories:
                                consolidation_candidates.append(group)
                                
            return consolidation_candidates
            
        except Exception as e:
            logger.error(f"Error finding consolidation candidates for user {user_id}: {str(e)}")
            return []
            
    async def consolidate_memory_group(self, user_id: int, memory_group: List[Dict[str, Any]]) -> Optional[int]:
        """
        Consolidate a group of memories into a single higher-level memory.

        Args:
            user_id (int): User ID
            memory_group (List[Dict[str, Any]]): Group of memories to consolidate

        Returns:
            Optional[int]: ID of the consolidated memory if successful, None otherwise
        """
        try:
            if not memory_group or len(memory_group) < 2:
                logger.warning("Not enough memories to consolidate")
                return None
                
            # Extract memory IDs and contents
            memory_ids = [memory["memory_id"] for memory in memory_group]
            memory_contents = [memory["content"] for memory in memory_group]
            category = memory_group[0]["category"]
            
            # Create a prompt for the AI to consolidate the memories
            consolidated_content = await self._generate_consolidated_content(memory_contents, category)
            
            if not consolidated_content:
                logger.warning(f"Failed to generate consolidated content for user {user_id}")
                return None
                
            # Calculate average importance, but slightly higher to reflect the consolidation
            avg_importance = min(5, int(sum(memory["importance"] for memory in memory_group) / len(memory_group)) + 1)
            
            # Create the consolidated memory
            consolidated_memory_id = await Memory.consolidate_memories(
                user_id=user_id,
                memory_ids=memory_ids,
                consolidated_content=consolidated_content,
                category=category,
                importance=avg_importance
            )
            
            if consolidated_memory_id:
                logger.info(f"Successfully consolidated {len(memory_group)} memories for user {user_id}")
            
            return consolidated_memory_id
            
        except Exception as e:
            logger.error(f"Error consolidating memories for user {user_id}: {str(e)}")
            return None
            
    async def _generate_consolidated_content(self, memory_contents: List[str], category: str) -> Optional[str]:
        """
        Generate consolidated content from multiple memory contents using AI.

        Args:
            memory_contents (List[str]): List of memory contents to consolidate
            category (str): Category of the memories

        Returns:
            Optional[str]: Consolidated content if successful, None otherwise
        """
        try:
            # Create a prompt for the AI to consolidate the memories
            memories_text = "\n".join([f"- {content}" for content in memory_contents])
            
            prompt = f"""
            You are an AI assistant that consolidates related memories into higher-level summaries.
            
            Below are several related memories in the category "{category}":
            
            {memories_text}
            
            Please create a single consolidated memory that captures the essential information from these individual memories.
            The consolidated memory should:
            1. Be concise (1-2 sentences)
            2. Capture the most important patterns or information
            3. Be more general than the individual memories
            4. Be written in a factual, declarative style
            
            Consolidated memory:
            """
            
            # Create a role context for memory consolidation
            consolidation_role_context = {
                "name": "Memory Consolidator",
                "personality": "Analytical and precise",
                "speaking_style": "Concise and structured",
                "knowledge_areas": "Information synthesis, pattern recognition",
                "behaviors": "Identifies patterns, summarizes effectively"
            }
            
            # Use model_manager with fallback capability
            response_tuple = await model_manager.generate_response(
                prompt=prompt,
                role_context=consolidation_role_context,
                temperature=0.3,  # Lower temperature for more consistent consolidation
                max_tokens=100,   # Short response
                use_fallbacks=True
            )
            
            # Extract response and model used
            response, model_used = response_tuple
            logger.info(f"Memory consolidation using model: {model_used}")
            
            # Clean up the response
            consolidated_content = response.strip()
            
            return consolidated_content
            
        except Exception as e:
            logger.error(f"Error generating consolidated content: {str(e)}")
            return None
            
    async def run_consolidation_cycle(self, user_id: int) -> List[int]:
        """
        Run a full consolidation cycle for a user.

        Args:
            user_id (int): User ID

        Returns:
            List[int]: List of consolidated memory IDs
        """
        try:
            # Find consolidation candidates
            consolidation_candidates = await self.find_consolidation_candidates(user_id)
            
            if not consolidation_candidates:
                logger.info(f"No consolidation candidates found for user {user_id}")
                return []
                
            # Consolidate each group
            consolidated_memory_ids = []
            for memory_group in consolidation_candidates:
                consolidated_memory_id = await self.consolidate_memory_group(user_id, memory_group)
                if consolidated_memory_id:
                    consolidated_memory_ids.append(consolidated_memory_id)
                    
            return consolidated_memory_ids
            
        except Exception as e:
            logger.error(f"Error running consolidation cycle for user {user_id}: {str(e)}")
            return []


# Create a singleton instance
memory_consolidator = MemoryConsolidator()
