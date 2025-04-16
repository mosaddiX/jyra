"""
Support module for Jyra.

This module provides functionality for managing user support tickets.
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Ensure the support tickets directory exists
SUPPORT_DIR = os.path.join(os.path.dirname(DATABASE_PATH), "support_tickets")
os.makedirs(SUPPORT_DIR, exist_ok=True)


class SupportTicket:
    """
    Class for managing support tickets.
    """

    # Status constants
    STATUS_OPEN = "open"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_RESOLVED = "resolved"
    STATUS_CLOSED = "closed"

    # Priority constants
    PRIORITY_LOW = "low"
    PRIORITY_MEDIUM = "medium"
    PRIORITY_HIGH = "high"
    PRIORITY_URGENT = "urgent"

    def __init__(self, ticket_id: Optional[int] = None, user_id: int = 0,
                 subject: str = "", description: str = "", 
                 status: str = STATUS_OPEN, priority: str = PRIORITY_MEDIUM,
                 created_at: Optional[str] = None,
                 updated_at: Optional[str] = None,
                 resolved_at: Optional[str] = None):
        """
        Initialize a SupportTicket object.

        Args:
            ticket_id (Optional[int]): Ticket ID
            user_id (int): User ID who created the ticket
            subject (str): Ticket subject
            description (str): Ticket description
            status (str): Ticket status
            priority (str): Ticket priority
            created_at (Optional[str]): When the ticket was created
            updated_at (Optional[str]): When the ticket was last updated
            resolved_at (Optional[str]): When the ticket was resolved
        """
        self.ticket_id = ticket_id
        self.user_id = user_id
        self.subject = subject
        self.description = description
        self.status = status
        self.priority = priority
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.resolved_at = resolved_at

    @classmethod
    async def create_ticket(cls, user_id: int, subject: str, description: str,
                           priority: str = PRIORITY_MEDIUM) -> Optional[int]:
        """
        Create a support ticket.

        Args:
            user_id (int): User ID
            subject (str): Ticket subject
            description (str): Ticket description
            priority (str): Ticket priority

        Returns:
            Optional[int]: Ticket ID if successful, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if support_tickets table exists, create if not
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS support_tickets (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subject TEXT,
                description TEXT,
                status TEXT DEFAULT 'open',
                priority TEXT DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # Create ticket_responses table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS ticket_responses (
                response_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id INTEGER,
                user_id INTEGER,
                is_staff BOOLEAN DEFAULT 0,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (ticket_id) REFERENCES support_tickets (ticket_id),
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
            """)

            # Insert ticket
            cursor.execute(
                """INSERT INTO support_tickets 
                   (user_id, subject, description, priority) 
                   VALUES (?, ?, ?, ?)""",
                (user_id, subject, description, priority)
            )

            # Get the inserted ticket ID
            ticket_id = cursor.lastrowid

            conn.commit()
            conn.close()

            # Also save to JSON file for easier tracking
            await cls._save_ticket_to_json(
                ticket_id, user_id, subject, description, priority
            )

            logger.info(f"Created support ticket '{subject}' from user {user_id}")
            return ticket_id

        except Exception as e:
            logger.error(f"Error creating support ticket from user {user_id}: {str(e)}")
            return None

    @classmethod
    async def get_tickets(cls, user_id: Optional[int] = None,
                         status: Optional[str] = None,
                         priority: Optional[str] = None,
                         limit: Optional[int] = None,
                         offset: int = 0) -> List['SupportTicket']:
        """
        Get support tickets.

        Args:
            user_id (Optional[int]): Filter by user ID
            status (Optional[str]): Filter by status
            priority (Optional[str]): Filter by priority
            limit (Optional[int]): Maximum number of tickets to retrieve
            offset (int): Offset for pagination

        Returns:
            List[SupportTicket]: List of SupportTicket objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if support_tickets table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets'"
            )
            if not cursor.fetchone():
                conn.close()
                return []

            query = """SELECT ticket_id, user_id, subject, description, status, priority, 
                       created_at, updated_at, resolved_at 
                       FROM support_tickets"""
            params = []
            conditions = []

            if user_id is not None:
                conditions.append("user_id = ?")
                params.append(user_id)

            if status:
                conditions.append("status = ?")
                params.append(status)

            if priority:
                conditions.append("priority = ?")
                params.append(priority)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY "
            if priority:
                query += "CASE priority "
                query += "WHEN 'urgent' THEN 1 "
                query += "WHEN 'high' THEN 2 "
                query += "WHEN 'medium' THEN 3 "
                query += "WHEN 'low' THEN 4 "
                query += "ELSE 5 END, "
            
            query += "created_at DESC"

            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()
            conn.close()

            return [
                cls(
                    ticket_id=row[0],
                    user_id=row[1],
                    subject=row[2],
                    description=row[3],
                    status=row[4],
                    priority=row[5],
                    created_at=row[6],
                    updated_at=row[7],
                    resolved_at=row[8]
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting support tickets: {str(e)}")
            return []

    @classmethod
    async def get_ticket(cls, ticket_id: int) -> Optional['SupportTicket']:
        """
        Get a specific support ticket.

        Args:
            ticket_id (int): Ticket ID

        Returns:
            Optional[SupportTicket]: SupportTicket object if found, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """SELECT ticket_id, user_id, subject, description, status, priority, 
                   created_at, updated_at, resolved_at 
                   FROM support_tickets WHERE ticket_id = ?""",
                (ticket_id,)
            )
            row = cursor.fetchone()
            conn.close()

            if not row:
                return None

            return cls(
                ticket_id=row[0],
                user_id=row[1],
                subject=row[2],
                description=row[3],
                status=row[4],
                priority=row[5],
                created_at=row[6],
                updated_at=row[7],
                resolved_at=row[8]
            )

        except Exception as e:
            logger.error(f"Error getting support ticket {ticket_id}: {str(e)}")
            return None

    @classmethod
    async def update_ticket(cls, ticket_id: int, 
                           status: Optional[str] = None,
                           priority: Optional[str] = None) -> bool:
        """
        Update a support ticket.

        Args:
            ticket_id (int): Ticket ID
            status (Optional[str]): New status
            priority (Optional[str]): New priority

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
                
                # If status is resolved, set resolved_at
                if status == cls.STATUS_RESOLVED:
                    update_parts.append("resolved_at = CURRENT_TIMESTAMP")

            if priority is not None:
                update_parts.append("priority = ?")
                params.append(priority)

            if not update_parts:
                conn.close()
                return False

            update_parts.append("updated_at = CURRENT_TIMESTAMP")
            
            query = f"UPDATE support_tickets SET {', '.join(update_parts)} WHERE ticket_id = ?"
            params.append(ticket_id)

            cursor.execute(query, params)
            conn.commit()
            conn.close()

            logger.info(f"Updated support ticket {ticket_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating support ticket {ticket_id}: {str(e)}")
            return False

    @classmethod
    async def add_response(cls, ticket_id: int, user_id: int, 
                          content: str, is_staff: bool = False) -> bool:
        """
        Add a response to a support ticket.

        Args:
            ticket_id (int): Ticket ID
            user_id (int): User ID
            content (str): Response content
            is_staff (bool): Whether the response is from staff

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Insert response
            cursor.execute(
                """INSERT INTO ticket_responses 
                   (ticket_id, user_id, is_staff, content) 
                   VALUES (?, ?, ?, ?)""",
                (ticket_id, user_id, 1 if is_staff else 0, content)
            )

            # Update ticket updated_at timestamp
            cursor.execute(
                "UPDATE support_tickets SET updated_at = CURRENT_TIMESTAMP WHERE ticket_id = ?",
                (ticket_id,)
            )

            conn.commit()
            conn.close()

            logger.info(f"Added response to support ticket {ticket_id} from user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error adding response to support ticket {ticket_id}: {str(e)}")
            return False

    @classmethod
    async def get_responses(cls, ticket_id: int) -> List[Dict[str, Any]]:
        """
        Get responses for a support ticket.

        Args:
            ticket_id (int): Ticket ID

        Returns:
            List[Dict[str, Any]]: List of responses
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """SELECT response_id, user_id, is_staff, content, created_at 
                   FROM ticket_responses 
                   WHERE ticket_id = ? 
                   ORDER BY created_at ASC""",
                (ticket_id,)
            )
            rows = cursor.fetchall()
            conn.close()

            return [
                {
                    "response_id": row[0],
                    "user_id": row[1],
                    "is_staff": bool(row[2]),
                    "content": row[3],
                    "created_at": row[4]
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting responses for support ticket {ticket_id}: {str(e)}")
            return []

    @classmethod
    async def get_support_stats(cls) -> Dict[str, Any]:
        """
        Get support ticket statistics.

        Returns:
            Dict[str, Any]: Support ticket statistics
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if support_tickets table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets'"
            )
            if not cursor.fetchone():
                conn.close()
                return {
                    "total": 0,
                    "by_status": {},
                    "by_priority": {},
                    "avg_resolution_time": 0,
                    "open_tickets": 0
                }

            # Get total count
            cursor.execute("SELECT COUNT(*) FROM support_tickets")
            total = cursor.fetchone()[0]

            # Get count by status
            cursor.execute(
                "SELECT status, COUNT(*) FROM support_tickets GROUP BY status"
            )
            by_status = {row[0]: row[1] for row in cursor.fetchall()}

            # Get count by priority
            cursor.execute(
                "SELECT priority, COUNT(*) FROM support_tickets GROUP BY priority"
            )
            by_priority = {row[0]: row[1] for row in cursor.fetchall()}

            # Get average resolution time (in hours)
            cursor.execute(
                """SELECT AVG((julianday(resolved_at) - julianday(created_at)) * 24) 
                   FROM support_tickets 
                   WHERE resolved_at IS NOT NULL"""
            )
            avg_resolution_time = cursor.fetchone()[0] or 0

            # Get open tickets count
            cursor.execute(
                "SELECT COUNT(*) FROM support_tickets WHERE status IN ('open', 'in_progress')"
            )
            open_tickets = cursor.fetchone()[0]

            conn.close()

            return {
                "total": total,
                "by_status": by_status,
                "by_priority": by_priority,
                "avg_resolution_time": round(avg_resolution_time, 1),
                "open_tickets": open_tickets
            }

        except Exception as e:
            logger.error(f"Error getting support stats: {str(e)}")
            return {
                "total": 0,
                "by_status": {},
                "by_priority": {},
                "avg_resolution_time": 0,
                "open_tickets": 0
            }

    @staticmethod
    async def _save_ticket_to_json(ticket_id: int, user_id: int, 
                                  subject: str, description: str,
                                  priority: str) -> None:
        """
        Save support ticket to a JSON file for easier tracking.

        Args:
            ticket_id (int): Ticket ID
            user_id (int): User ID
            subject (str): Ticket subject
            description (str): Ticket description
            priority (str): Ticket priority
        """
        try:
            # Create a filename with date prefix for organization
            date_prefix = datetime.now().strftime("%Y%m%d")
            filename = f"{date_prefix}_ticket_{ticket_id}.json"
            filepath = os.path.join(SUPPORT_DIR, filename)

            # Prepare the data
            data = {
                "ticket_id": ticket_id,
                "user_id": user_id,
                "subject": subject,
                "description": description,
                "status": "open",
                "priority": priority,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "resolved_at": None
            }

            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving support ticket to JSON: {str(e)}")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the support ticket to a dictionary.

        Returns:
            Dict[str, Any]: Support ticket data as a dictionary
        """
        return {
            "ticket_id": self.ticket_id,
            "user_id": self.user_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "resolved_at": self.resolved_at
        }
