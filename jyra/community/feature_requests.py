"""
Feature request module for Jyra.

This module provides functionality for managing feature requests.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ensure the feature requests directory exists
FEATURE_REQUESTS_DIR = os.path.join(os.path.dirname(DATABASE_PATH), "feature_requests")
os.makedirs(FEATURE_REQUESTS_DIR, exist_ok=True)


class FeatureRequest:
    """
    Class for managing feature requests.
    """

    # Status constants
    STATUS_NEW = "new"
    STATUS_UNDER_REVIEW = "under_review"
    STATUS_PLANNED = "planned"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_DECLINED = "declined"

    def __init__(self, request_id: Optional[int] = None, user_id: int = 0,
                 title: str = "", description: str = "", status: str = STATUS_NEW,
                 votes: int = 0, created_at: Optional[str] = None,
                 updated_at: Optional[str] = None):
        """
        Initialize a FeatureRequest object.

        Args:
            request_id (Optional[int]): Request ID
            user_id (int): User ID who requested the feature
            title (str): Feature title
            description (str): Feature description
            status (str): Request status
            votes (int): Number of votes
            created_at (Optional[str]): When the request was created
            updated_at (Optional[str]): When the request was last updated
        """
        self.request_id = request_id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.status = status
        self.votes = votes
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at

    @classmethod
    async def add_feature_request(cls, user_id: int, title: str, 
                                 description: str) -> Optional[int]:
        """
        Add a feature request.

        Args:
            user_id (int): User ID
            title (str): Feature title
            description (str): Feature description

        Returns:
            Optional[int]: Request ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if feature_requests table exists, create if not
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_requests (
                request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                description TEXT,
                status TEXT DEFAULT 'new',
                votes INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # Create votes table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS feature_request_votes (
                vote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (request_id) REFERENCES feature_requests (request_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(request_id, user_id)
            )
            """)

            # Insert feature request
            cursor.execute(
                """INSERT INTO feature_requests 
                   (user_id, title, description) 
                   VALUES (?, ?, ?)""",
                (user_id, title, description)
            )

            # Get the inserted request ID
            request_id = cursor.lastrowid

            conn.commit()
            conn.close()

            # Also save to JSON file for easier tracking
            await cls._save_request_to_json(
                request_id, user_id, title, description
            )

            logger.info(f"Added feature request '{title}' from user {user_id}")
            return request_id

        except Exception as e:
            logger.error(f"Error adding feature request from user {user_id}: {str(e)}")
            return None

    @classmethod
    async def get_feature_requests(cls, status: Optional[str] = None,
                                  limit: Optional[int] = None,
                                  offset: int = 0) -> List['FeatureRequest']:
        """
        Get feature requests.

        Args:
            status (Optional[str]): Filter by status
            limit (Optional[int]): Maximum number of requests to retrieve
            offset (int): Offset for pagination

        Returns:
            List[FeatureRequest]: List of FeatureRequest objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if feature_requests table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='feature_requests'"
            )
            if not cursor.fetchone():
                conn.close()
                return []

            query = """SELECT request_id, user_id, title, description, status, votes, 
                       created_at, updated_at 
                       FROM feature_requests"""
            params = []

            if status:
                query += " WHERE status = ?"
                params.append(status)

            query += " ORDER BY votes DESC, created_at DESC"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                cls(
                    request_id=row[0],
                    user_id=row[1],
                    title=row[2],
                    description=row[3],
                    status=row[4],
                    votes=row[5],
                    created_at=row[6],
                    updated_at=row[7]
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting feature requests: {str(e)}")
            return []

    @classmethod
    async def get_feature_request(cls, request_id: int) -> Optional['FeatureRequest']:
        """
        Get a specific feature request.

        Args:
            request_id (int): Request ID

        Returns:
            Optional[FeatureRequest]: FeatureRequest object if found, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """SELECT request_id, user_id, title, description, status, votes, 
                   created_at, updated_at 
                   FROM feature_requests WHERE request_id = ?""",
                (request_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return cls(
                request_id=row[0],
                user_id=row[1],
                title=row[2],
                description=row[3],
                status=row[4],
                votes=row[5],
                created_at=row[6],
                updated_at=row[7]
            )

        except Exception as e:
            logger.error(f"Error getting feature request {request_id}: {str(e)}")
            return None

    @classmethod
    async def update_feature_request(cls, request_id: int, 
                                    status: Optional[str] = None,
                                    title: Optional[str] = None,
                                    description: Optional[str] = None) -> bool:
        """
        Update a feature request.

        Args:
            request_id (int): Request ID
            status (Optional[str]): New status
            title (Optional[str]): New title
            description (Optional[str]): New description

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Build the update query
            update_parts = []
            params = []

            if status is not None:
                update_parts.append("status = ?")
                params.append(status)

            if title is not None:
                update_parts.append("title = ?")
                params.append(title)

            if description is not None:
                update_parts.append("description = ?")
                params.append(description)

            if not update_parts:
                conn.close()
                return False

            update_parts.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE feature_requests SET {', '.join(update_parts)} WHERE request_id = ?"
            params.append(request_id)

            cursor.execute(query, params)
            conn.commit()
            conn.close()

            logger.info(f"Updated feature request {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating feature request {request_id}: {str(e)}")
            return False

    @classmethod
    async def vote_for_feature(cls, request_id: int, user_id: int) -> bool:
        """
        Vote for a feature request.

        Args:
            request_id (int): Request ID
            user_id (int): User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if user already voted
            cursor.execute(
                "SELECT vote_id FROM feature_request_votes WHERE request_id = ? AND user_id = ?",
                (request_id, user_id)
            )
            if cursor.fetchone():
                conn.close()
                return False  # Already voted

            # Add vote
            cursor.execute(
                "INSERT INTO feature_request_votes (request_id, user_id) VALUES (?, ?)",
                (request_id, user_id)
            )

            # Update vote count
            cursor.execute(
                """UPDATE feature_requests 
                   SET votes = (SELECT COUNT(*) FROM feature_request_votes WHERE request_id = ?),
                       updated_at = CURRENT_TIMESTAMP
                   WHERE request_id = ?""",
                (request_id, request_id)
            )

            conn.commit()
            conn.close()

            logger.info(f"User {user_id} voted for feature request {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error voting for feature request {request_id}: {str(e)}")
            return False

    @classmethod
    async def remove_vote(cls, request_id: int, user_id: int) -> bool:
        """
        Remove a vote from a feature request.

        Args:
            request_id (int): Request ID
            user_id (int): User ID

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Remove vote
            cursor.execute(
                "DELETE FROM feature_request_votes WHERE request_id = ? AND user_id = ?",
                (request_id, user_id)
            )

            if cursor.rowcount == 0:
                conn.close()
                return False  # No vote to remove

            # Update vote count
            cursor.execute(
                """UPDATE feature_requests 
                   SET votes = (SELECT COUNT(*) FROM feature_request_votes WHERE request_id = ?),
                       updated_at = CURRENT_TIMESTAMP
                   WHERE request_id = ?""",
                (request_id, request_id)
            )

            conn.commit()
            conn.close()

            logger.info(f"User {user_id} removed vote from feature request {request_id}")
            return True

        except Exception as e:
            logger.error(f"Error removing vote from feature request {request_id}: {str(e)}")
            return False

    @classmethod
    async def get_feature_request_stats(cls) -> Dict[str, Any]:
        """
        Get feature request statistics.

        Returns:
            Dict[str, Any]: Feature request statistics
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if feature_requests table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='feature_requests'"
            )
            if not cursor.fetchone():
                conn.close()
                return {
                    "total": 0,
                    "by_status": {},
                    "top_voted": [],
                    "recent": []
                }

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM feature_requests")
            total = cursor.fetchone()[0]

            # Get count by status
            cursor.execute(
                "SELECT status, COUNT(*) FROM feature_requests GROUP BY status"
            )
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # Get top voted requests
            cursor.execute(
                """SELECT request_id, title, votes 
                   FROM feature_requests 
                   ORDER BY votes DESC LIMIT 5"""
            )
            top_voted = [
                {"id": row[0], "title": row[1], "votes": row[2]}
                for row in cursor.fetchall()
            ]

            # Get recent requests
            cursor.execute(
                """SELECT request_id, title, created_at 
                   FROM feature_requests 
                   ORDER BY created_at DESC LIMIT 5"""
            )
            recent = [
                {"id": row[0], "title": row[1], "created_at": row[2]}
                for row in cursor.fetchall()
            ]

            conn.close()

            return {
                "total": total,
                "by_status": by_status,
                "top_voted": top_voted,
                "recent": recent
            }

        except Exception as e:
            logger.error(f"Error getting feature request stats: {str(e)}")
            return {
                "total": 0,
                "by_status": {},
                "top_voted": [],
                "recent": []
            }

    @staticmethod
    async def _save_request_to_json(request_id: int, user_id: int, 
                                   title: str, description: str) -> None:
        """
        Save feature request to a JSON file for easier tracking.

        Args:
            request_id (int): Request ID
            user_id (int): User ID
            title (str): Feature title
            description (str): Feature description
        """
        try:
            # Create a filename with date prefix for organization
            date_prefix = datetime.now().strftime("%Y%m%d")
            filename = f"{date_prefix}_request_{request_id}.json"
            filepath = os.path.join(FEATURE_REQUESTS_DIR, filename)

            # Prepare the data
            data = {
                "request_id": request_id,
                "user_id": user_id,
                "title": title,
                "description": description,
                "status": "new",
                "votes": 0,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving feature request to JSON: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the feature request to a dictionary.

        Returns:
            Dict[str, Any]: Feature request data as a dictionary
        """
        return {
            "request_id": self.request_id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "votes": self.votes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
