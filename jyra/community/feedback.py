"""
Feedback collection module for Jyra.

This module provides functionality for collecting and managing user feedback.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ensure the feedback directory exists
FEEDBACK_DIR = os.path.join(os.path.dirname(DATABASE_PATH), "feedback")
os.makedirs(FEEDBACK_DIR, exist_ok=True)


class Feedback:
    """
    Class for managing user feedback.
    """

    def __init__(self, feedback_id: Optional[int] = None, user_id: int = 0,
                 feedback_type: str = "", content: str = "", rating: int = 0,
                 created_at: Optional[str] = None):
        """
        Initialize a Feedback object.

        Args:
            feedback_id (Optional[int]): Feedback ID
            user_id (int): User ID who provided the feedback
            feedback_type (str): Type of feedback (bug, feature, general)
            content (str): Feedback content
            rating (int): Rating (1-5)
            created_at (Optional[str]): When the feedback was created
        """
        self.feedback_id = feedback_id
        self.user_id = user_id
        self.feedback_type = feedback_type
        self.content = content
        self.rating = rating
        self.created_at = created_at or datetime.now().isoformat()

    @classmethod
    async def add_feedback(cls, user_id: int, feedback_type: str, content: str,
                          rating: int = 0) -> bool:
        """
        Add feedback from a user.

        Args:
            user_id (int): User ID
            feedback_type (str): Type of feedback (bug, feature, general)
            content (str): Feedback content
            rating (int): Rating (1-5)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if feedback table exists, create if not
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                feedback_type TEXT,
                content TEXT,
                rating INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # Insert feedback
            cursor.execute(
                """INSERT INTO feedback 
                   (user_id, feedback_type, content, rating) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, feedback_type, content, rating)
            )

            # Get the inserted feedback ID
            feedback_id = cursor.lastrowid

            conn.commit()
            conn.close()

            # Also save to JSON file for easier analysis
            await cls._save_feedback_to_json(
                feedback_id, user_id, feedback_type, content, rating
            )

            logger.info(f"Added {feedback_type} feedback from user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding feedback from user {user_id}: {str(e)}")
            return False

    @classmethod
    async def get_feedback(cls, feedback_type: Optional[str] = None,
                          limit: Optional[int] = None) -> List['Feedback']:
        """
        Get feedback entries.

        Args:
            feedback_type (Optional[str]): Filter by feedback type
            limit (Optional[int]): Maximum number of entries to retrieve

        Returns:
            List[Feedback]: List of Feedback objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if feedback table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'"
            )
            if not cursor.fetchone():
                conn.close()
                return []

            query = """SELECT feedback_id, user_id, feedback_type, content, rating, created_at 
                       FROM feedback"""
            params = []

            if feedback_type:
                query += " WHERE feedback_type = ?"
                params.append(feedback_type)

            query += " ORDER BY created_at DESC"

            if limit:
                query += " LIMIT ?"
                params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                cls(
                    feedback_id=row[0],
                    user_id=row[1],
                    feedback_type=row[2],
                    content=row[3],
                    rating=row[4],
                    created_at=row[5]
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting feedback: {str(e)}")
            return []

    @classmethod
    async def get_feedback_stats(cls) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Returns:
            Dict[str, Any]: Feedback statistics
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if feedback table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback'"
            )
            if not cursor.fetchone():
                conn.close()
                return {
                    "total": 0,
                    "by_type": {},
                    "average_rating": 0,
                    "recent_count": 0
                }

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM feedback")
            total = cursor.fetchone()[0]

            # Get count by type
            cursor.execute(
                "SELECT feedback_type, COUNT(*) FROM feedback GROUP BY feedback_type"
            )
            by_type = {row[0]: row[1] for row in cursor.fetchall()}

            # Get average rating
            cursor.execute(
                "SELECT AVG(rating) FROM feedback WHERE rating > 0"
            )
            avg_rating = cursor.fetchone()[0] or 0

            # Get recent count (last 30 days)
            cursor.execute(
                "SELECT COUNT(*) FROM feedback WHERE created_at > datetime('now', '-30 days')"
            )
            recent_count = cursor.fetchone()[0]

            conn.close()

            return {
                "total": total,
                "by_type": by_type,
                "average_rating": round(avg_rating, 1),
                "recent_count": recent_count
            }

        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "total": 0,
                "by_type": {},
                "average_rating": 0,
                "recent_count": 0
            }

    @staticmethod
    async def _save_feedback_to_json(feedback_id: int, user_id: int, 
                                    feedback_type: str, content: str,
                                    rating: int) -> None:
        """
        Save feedback to a JSON file for easier analysis.

        Args:
            feedback_id (int): Feedback ID
            user_id (int): User ID
            feedback_type (str): Type of feedback
            content (str): Feedback content
            rating (int): Rating
        """
        try:
            # Create a filename with date prefix for organization
            date_prefix = datetime.now().strftime("%Y%m%d")
            filename = f"{date_prefix}_{feedback_type}_{feedback_id}.json"
            filepath = os.path.join(FEEDBACK_DIR, filename)

            # Prepare the data
            data = {
                "feedback_id": feedback_id,
                "user_id": user_id,
                "feedback_type": feedback_type,
                "content": content,
                "rating": rating,
                "created_at": datetime.now().isoformat()
            }

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving feedback to JSON: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the feedback to a dictionary.

        Returns:
            Dict[str, Any]: Feedback data as a dictionary
        """
        return {
            "feedback_id": self.feedback_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type,
            "content": self.content,
            "rating": self.rating,
            "created_at": self.created_at
        }
