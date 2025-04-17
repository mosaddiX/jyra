"""
Role model for Jyra
"""

import json
import sqlite3
from typing import List, Dict, Any, Optional

from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger
from jyra.roles.templates.default_roles import DEFAULT_ROLES

logger = setup_logger(__name__)


class Role:
    """
    Class for managing role data in the database.
    """

    def __init__(self, role_id: Optional[int] = None, name: str = "", description: str = "",
                 personality: str = "", speaking_style: str = "",
                 knowledge_areas: str = "", behaviors: str = "",
                 is_custom: bool = False, created_by: Optional[int] = None,
                 is_featured: bool = False, is_popular: bool = False):
        """
        Initialize a Role object.

        Args:
            role_id (Optional[int]): Role ID
            name (str): Role name
            description (str): Role description
            personality (str): Role personality traits
            speaking_style (str): Role speaking style
            knowledge_areas (str): Role knowledge areas
            behaviors (str): Role behaviors
            is_custom (bool): Whether this is a custom role
            created_by (Optional[int]): User ID who created this role
        """
        self.role_id = role_id
        self.name = name
        self.description = description
        self.personality = personality
        self.speaking_style = speaking_style
        self.knowledge_areas = knowledge_areas
        self.behaviors = behaviors
        self.is_custom = is_custom
        self.created_by = created_by
        self.is_featured = is_featured
        self.is_popular = is_popular

    @classmethod
    async def initialize_default_roles(cls) -> bool:
        """
        Initialize the default roles in the database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if roles already exist
            cursor.execute("SELECT COUNT(*) FROM roles WHERE is_custom = 0")
            count = cursor.fetchone()[0]

            if count > 0:
                logger.info("Default roles already initialized")
                conn.close()
                return True

            # Insert default roles
            for role_key, role_data in DEFAULT_ROLES.items():
                cursor.execute(
                    "INSERT INTO roles (name, description, personality, speaking_style, "
                    "knowledge_areas, behaviors, is_custom, is_featured, is_popular) VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)",
                    (
                        role_data["name"],
                        role_data["description"],
                        role_data["personality"],
                        role_data["speaking_style"],
                        role_data["knowledge_areas"],
                        role_data["behaviors"],
                        int(role_data.get("is_featured", 0)),
                        int(role_data.get("is_popular", 0))
                    )
                )

            conn.commit()
            conn.close()

            logger.info(f"Initialized {len(DEFAULT_ROLES)} default roles")
            return True

        except Exception as e:
            logger.error(f"Error initializing default roles: {str(e)}")
            return False

    @classmethod
    async def get_role(cls, role_id: int) -> Optional['Role']:
        """
        Get a role from the database by role_id.

        Args:
            role_id (int): Role ID

        Returns:
            Optional[Role]: Role object if found, None otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT role_id, name, description, personality, speaking_style, "
                "knowledge_areas, behaviors, is_custom, created_by, is_featured, is_popular "
                "FROM roles WHERE role_id = ?",
                (role_id,)
            )

            row = cursor.fetchone()
            conn.close()

            if row:
                return cls(
                    role_id=row[0],
                    name=row[1],
                    description=row[2],
                    personality=row[3],
                    speaking_style=row[4],
                    knowledge_areas=row[5],
                    behaviors=row[6],
                    is_custom=bool(row[7]),
                    created_by=row[8],
                    is_featured=bool(row[9]),
                    is_popular=bool(row[10])
                )

            return None

        except Exception as e:
            logger.error(f"Error getting role {role_id}: {str(e)}")
            return None

    @classmethod
    async def get_all_roles(cls, include_custom: bool = True,
                            created_by: Optional[int] = None) -> List['Role']:
        """
        Get all roles from the database.

        Args:
            include_custom (bool): Whether to include custom roles
            created_by (Optional[int]): Filter custom roles by creator

        Returns:
            List[Role]: List of Role objects
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            query = "SELECT role_id, name, description, personality, speaking_style, " \
                    "knowledge_areas, behaviors, is_custom, created_by, is_featured, is_popular FROM roles"

            params = []
            conditions = []

            if not include_custom:
                conditions.append("is_custom = 0")

            if created_by is not None:
                conditions.append("(is_custom = 0 OR created_by = ?)")
                params.append(created_by)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY is_custom, name"

            cursor.execute(query, params)

            rows = cursor.fetchall()
            conn.close()

            return [
                cls(
                    role_id=row[0],
                    name=row[1],
                    description=row[2],
                    personality=row[3],
                    speaking_style=row[4],
                    knowledge_areas=row[5],
                    behaviors=row[6],
                    is_custom=bool(row[7]),
                    created_by=row[8],
                    is_featured=bool(row[9]) if len(row) > 9 else False,
                    is_popular=bool(row[10]) if len(row) > 10 else False
                )
                for row in rows
            ]

        except Exception as e:
            logger.error(f"Error getting all roles: {str(e)}")
            return []

    async def save(self) -> bool:
        """
        Save the role to the database.

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            if self.role_id is None:
                # Insert new role
                cursor.execute(
                    "INSERT INTO roles (name, description, personality, speaking_style, "
                    "knowledge_areas, behaviors, is_custom, created_by) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        self.name,
                        self.description,
                        self.personality,
                        self.speaking_style,
                        self.knowledge_areas,
                        self.behaviors,
                        1 if self.is_custom else 0,
                        self.created_by
                    )
                )

                self.role_id = cursor.lastrowid
            else:
                # Update existing role
                cursor.execute(
                    "UPDATE roles SET name = ?, description = ?, personality = ?, "
                    "speaking_style = ?, knowledge_areas = ?, behaviors = ? "
                    "WHERE role_id = ?",
                    (
                        self.name,
                        self.description,
                        self.personality,
                        self.speaking_style,
                        self.knowledge_areas,
                        self.behaviors,
                        self.role_id
                    )
                )

            conn.commit()
            conn.close()

            logger.info(
                f"Role {self.name} saved successfully with ID {self.role_id}")
            return True

        except Exception as e:
            logger.error(f"Error saving role {self.name}: {str(e)}")
            return False

    @classmethod
    async def delete_role(cls, role_id: int, user_id: Optional[int] = None) -> bool:
        """
        Delete a role from the database.

        Args:
            role_id (int): Role ID to delete
            user_id (Optional[int]): User ID requesting deletion (for permission check)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Check if role exists and is custom
            cursor.execute(
                "SELECT is_custom, created_by FROM roles WHERE role_id = ?",
                (role_id,)
            )

            row = cursor.fetchone()

            if not row:
                logger.warning(f"Role {role_id} not found for deletion")
                conn.close()
                return False

            is_custom, created_by = row

            # Only allow deletion of custom roles
            if not is_custom:
                logger.warning(f"Cannot delete default role {role_id}")
                conn.close()
                return False

            # Check if user has permission to delete this role
            if user_id is not None and created_by != user_id:
                logger.warning(
                    f"User {user_id} does not have permission to delete role {role_id}")
                conn.close()
                return False

            # Delete the role
            cursor.execute("DELETE FROM roles WHERE role_id = ?", (role_id,))

            # Update users who were using this role
            cursor.execute(
                "UPDATE users SET current_role_id = NULL WHERE current_role_id = ?",
                (role_id,)
            )

            conn.commit()
            conn.close()

            logger.info(f"Role {role_id} deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting role {role_id}: {str(e)}")
            return False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the role to a dictionary.

        Returns:
            Dict[str, Any]: Role data as a dictionary
        """
        return {
            "role_id": self.role_id,
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "speaking_style": self.speaking_style,
            "knowledge_areas": self.knowledge_areas,
            "behaviors": self.behaviors,
            "is_custom": self.is_custom,
            "created_by": self.created_by,
            "is_featured": self.is_featured,
            "is_popular": self.is_popular
        }
