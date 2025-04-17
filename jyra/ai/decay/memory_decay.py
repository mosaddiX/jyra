"""
Memory decay module for Jyra.

This module provides functionality to gradually reduce the importance of memories over time.
"""

import sqlite3
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

from jyra.db.models.memory import Memory
from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class MemoryDecay:
    """
    Class for managing memory decay.
    """
    
    def __init__(self):
        """
        Initialize the memory decay manager.
        """
        logger.info("Initializing memory decay manager")
    
    async def apply_decay_to_user_memories(self, 
                                         user_id: int, 
                                         decay_factor: float = 0.9,
                                         min_age_days: int = 30,
                                         min_importance: int = 2,
                                         max_decay_per_run: int = 10) -> Dict[str, Any]:
        """
        Apply decay to a user's memories based on age and access patterns.
        
        Args:
            user_id (int): User ID
            decay_factor (float): Factor to multiply importance by (0.0-1.0)
            min_age_days (int): Minimum age in days for memories to be considered for decay
            min_importance (int): Minimum importance level to consider for decay
            max_decay_per_run (int): Maximum number of memories to decay in one run
            
        Returns:
            Dict[str, Any]: Results of the decay process
        """
        try:
            # Get candidate memories for decay
            candidates = await self._get_decay_candidates(
                user_id=user_id,
                min_age_days=min_age_days,
                min_importance=min_importance,
                limit=max_decay_per_run
            )
            
            if not candidates:
                logger.info(f"No decay candidates found for user {user_id}")
                return {
                    "success": True,
                    "decayed_count": 0,
                    "message": "No memories suitable for decay were found."
                }
            
            # Apply decay to each candidate
            decayed_count = 0
            decayed_memory_ids = []
            
            for memory in candidates:
                # Calculate new importance
                new_importance = max(1, math.floor(memory.importance * decay_factor))
                
                # Only count as decayed if importance actually changed
                if new_importance < memory.importance:
                    # Update the memory importance
                    success = await self._update_memory_importance(
                        memory_id=memory.memory_id,
                        new_importance=new_importance
                    )
                    
                    if success:
                        decayed_count += 1
                        decayed_memory_ids.append(memory.memory_id)
            
            return {
                "success": True,
                "decayed_count": decayed_count,
                "decayed_memory_ids": decayed_memory_ids,
                "message": f"Successfully decayed {decayed_count} memories."
            }
            
        except Exception as e:
            logger.error(f"Error applying decay to user memories: {str(e)}")
            return {
                "success": False,
                "decayed_count": 0,
                "message": f"Error applying decay: {str(e)}"
            }
    
    async def _get_decay_candidates(self, 
                                  user_id: int, 
                                  min_age_days: int = 30,
                                  min_importance: int = 2,
                                  limit: int = 10) -> List[Memory]:
        """
        Get memories that are candidates for decay.
        
        Args:
            user_id (int): User ID
            min_age_days (int): Minimum age in days for memories to be considered for decay
            min_importance (int): Minimum importance level to consider for decay
            limit (int): Maximum number of memories to retrieve
            
        Returns:
            List[Memory]: List of memory candidates for decay
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Calculate the cutoff date
            cutoff_date = (datetime.now() - timedelta(days=min_age_days)).strftime("%Y-%m-%d %H:%M:%S")
            
            # Query for decay candidates
            # Prioritize:
            # 1. Older memories
            # 2. Less frequently accessed memories
            # 3. Non-consolidated memories
            query = """
                SELECT memory_id, user_id, content, category, importance, source, context,
                       last_accessed, created_at, confidence, expires_at, recall_count,
                       last_reinforced, is_consolidated
                FROM memories
                WHERE user_id = ?
                AND importance >= ?
                AND created_at < ?
                AND (is_consolidated = 0 OR is_consolidated IS NULL)
                ORDER BY 
                    last_accessed ASC,
                    recall_count ASC,
                    created_at ASC
                LIMIT ?
            """
            
            cursor.execute(query, (user_id, min_importance, cutoff_date, limit))
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
            
            # Create Memory objects
            memories = []
            for row in rows:
                memory_id = row[0]
                memory = Memory(
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
            logger.error(f"Error getting decay candidates: {str(e)}")
            return []
    
    async def _update_memory_importance(self, memory_id: int, new_importance: int) -> bool:
        """
        Update the importance of a memory.
        
        Args:
            memory_id (int): Memory ID
            new_importance (int): New importance level
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            # Update the memory importance
            cursor.execute(
                """UPDATE memories SET 
                   importance = ?,
                   context = CASE 
                       WHEN context IS NULL THEN ? 
                       ELSE context || ' | ' || ? 
                   END
                   WHERE memory_id = ?""",
                (new_importance, 
                 f"Importance decayed to {new_importance}", 
                 f"Importance decayed to {new_importance}", 
                 memory_id)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated importance of memory {memory_id} to {new_importance}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating memory importance: {str(e)}")
            return False
    
    async def run_scheduled_decay(self, 
                                decay_factor: float = 0.9,
                                min_age_days: int = 30,
                                min_importance: int = 2,
                                max_per_user: int = 5) -> Dict[str, Any]:
        """
        Run scheduled decay for all users.
        
        Args:
            decay_factor (float): Factor to multiply importance by (0.0-1.0)
            min_age_days (int): Minimum age in days for memories to be considered for decay
            min_importance (int): Minimum importance level to consider for decay
            max_per_user (int): Maximum number of memories to decay per user
            
        Returns:
            Dict[str, Any]: Results of the decay process
        """
        try:
            # Get all users
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT user_id FROM memories")
            user_ids = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            if not user_ids:
                logger.info("No users found for scheduled decay")
                return {
                    "success": True,
                    "users_processed": 0,
                    "total_decayed": 0,
                    "message": "No users found for scheduled decay."
                }
            
            # Apply decay to each user's memories
            total_decayed = 0
            users_with_decay = 0
            
            for user_id in user_ids:
                result = await self.apply_decay_to_user_memories(
                    user_id=user_id,
                    decay_factor=decay_factor,
                    min_age_days=min_age_days,
                    min_importance=min_importance,
                    max_decay_per_run=max_per_user
                )
                
                if result["success"] and result["decayed_count"] > 0:
                    total_decayed += result["decayed_count"]
                    users_with_decay += 1
            
            return {
                "success": True,
                "users_processed": len(user_ids),
                "users_with_decay": users_with_decay,
                "total_decayed": total_decayed,
                "message": f"Successfully decayed {total_decayed} memories across {users_with_decay} users."
            }
            
        except Exception as e:
            logger.error(f"Error running scheduled decay: {str(e)}")
            return {
                "success": False,
                "users_processed": 0,
                "total_decayed": 0,
                "message": f"Error running scheduled decay: {str(e)}"
            }


# Create a singleton instance
memory_decay = MemoryDecay()
