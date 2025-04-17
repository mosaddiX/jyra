"""
Button factory functions for Jyra bot.

This module provides functions for creating consistent buttons
throughout the bot interface.
"""

from typing import List, Optional, Union, Any
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def create_button(text: str, callback_data: Optional[str] = None,
                  url: Optional[str] = None) -> InlineKeyboardButton:
    """
    Create a button with consistent styling.

    Args:
        text: The button text
        callback_data: Optional callback data for the button
        url: Optional URL for the button

    Returns:
        An InlineKeyboardButton instance
    """
    if url:
        return InlineKeyboardButton(text=text, url=url)
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def create_callback_button(text: str, callback_data: str) -> InlineKeyboardButton:
    """
    Create a callback button with consistent styling.

    Args:
        text: The button text
        callback_data: The callback data for the button

    Returns:
        An InlineKeyboardButton instance
    """
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def create_url_button(text: str, url: str) -> InlineKeyboardButton:
    """
    Create a URL button with consistent styling.

    Args:
        text: The button text
        url: The URL for the button

    Returns:
        An InlineKeyboardButton instance
    """
    return InlineKeyboardButton(text=text, url=url)


def create_button_row(buttons: List[InlineKeyboardButton]) -> List[InlineKeyboardButton]:
    """
    Create a row of buttons.

    Args:
        buttons: List of buttons to include in the row

    Returns:
        A list of buttons representing a row
    """
    return buttons


def create_button_grid(buttons: List[InlineKeyboardButton],
                       columns: int = 2) -> List[List[InlineKeyboardButton]]:
    """
    Create a grid of buttons with the specified number of columns.

    Args:
        buttons: List of buttons to include in the grid
        columns: Number of columns in the grid

    Returns:
        A list of button rows
    """
    return [buttons[i:i+columns] for i in range(0, len(buttons), columns)]


def create_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Create the main menu keyboard.

    Returns:
        An InlineKeyboardMarkup instance with the main menu buttons
    """
    keyboard = [
        [
            create_callback_button("🎭 Roles", "menu_roles"),
            create_callback_button("🧠 Memory", "menu_memory")
        ],
        [
            create_callback_button("⚙️ Settings", "menu_settings"),
            create_callback_button("❓ Help", "menu_help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_role_selection_keyboard(roles: List[dict],
                                   page: int = 0,
                                   page_size: int = 6,
                                   filter_type: str = None,
                                   category: str = None) -> InlineKeyboardMarkup:
    """
    Create a paginated role selection keyboard with filters and categories.

    Args:
        roles: List of role dictionaries (should include 'is_featured', 'is_popular', 'is_custom', 'category')
        page: Current page number (0-indexed)
        page_size: Number of roles per page
        filter_type: 'featured', 'popular', 'custom', or None
        category: Filter by category name
    Returns:
        An InlineKeyboardMarkup instance with role selection buttons
    """
    # Filter roles if needed
    filtered_roles = roles
    if filter_type == 'featured':
        filtered_roles = [r for r in roles if r.get('is_featured')]
    elif filter_type == 'popular':
        filtered_roles = [r for r in roles if r.get('is_popular')]
    elif filter_type == 'custom':
        filtered_roles = [r for r in roles if r.get('is_custom')]

    # Filter by category if specified
    if category:
        filtered_roles = [
            r for r in filtered_roles if r.get('category') == category]

    # Sort: featured first, then popular, then by category, then by name
    def sort_key(role):
        return (
            -int(role.get('is_featured', False)),
            -int(role.get('is_popular', False)),
            role.get('category', 'General'),
            role.get('name', '').lower()
        )
    filtered_roles = sorted(filtered_roles, key=sort_key)

    # Calculate pagination
    total_pages = (len(filtered_roles) + page_size -
                   1) // page_size if filtered_roles else 1
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(filtered_roles))

    keyboard = []
    current_row = []
    for i in range(start_idx, end_idx):
        role = filtered_roles[i]
        emoji = role.get('emoji', '')
        prefix = ''
        if role.get('is_featured'):
            prefix += '🌟'
        if role.get('is_popular'):
            prefix += '🔥'
        if role.get('is_custom'):
            prefix += '📝'
        button = create_callback_button(
            f"{prefix}{emoji} {role['name']}",
            f"role_{role['role_id']}"
        )
        current_row.append(button)
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []
    if current_row:
        keyboard.append(current_row)

    # Filter/section buttons
    filter_row = [
        create_callback_button("🌟 Featured", "roles_filter_featured"),
        create_callback_button("🔥 Popular", "roles_filter_popular")
    ]

    # Add categories button
    filter_row.append(create_callback_button(
        "📂 Categories", "roles_categories"))
    keyboard.append(filter_row)

    # Navigation row
    nav_row = []
    if page > 0:
        nav_row.append(create_callback_button(
            "⬅️ Previous", f"roles_page_{page-1}"))
    if page < total_pages - 1:
        nav_row.append(create_callback_button(
            "➡️ Next", f"roles_page_{page+1}"))
    if nav_row:
        keyboard.append(nav_row)

    # Add create role button
    keyboard.append([create_callback_button(
        "➕ Create Custom Role", "create_role")])

    # Add back button
    keyboard.append([create_callback_button("⬅️ Back to Menu", "menu_main")])
    return InlineKeyboardMarkup(keyboard)


def create_settings_keyboard(show_profiles: bool = False) -> InlineKeyboardMarkup:
    """
    Create the settings menu keyboard.

    Args:
        show_profiles: Whether to show the settings profiles view

    Returns:
        An InlineKeyboardMarkup instance with settings buttons
    """
    if show_profiles:
        # Show settings profiles view
        keyboard = [
            [
                create_callback_button(
                    "📝 Save Current Settings", "settings_profile_save")
            ],
            [
                create_callback_button(
                    "💾 Default Profile", "settings_profile_load_default"),
                create_callback_button(
                    "📂 Custom Profile", "settings_profile_load_custom")
            ],
            [
                create_callback_button(
                    "📚 Professional", "settings_profile_load_professional"),
                create_callback_button(
                    "🌟 Creative", "settings_profile_load_creative")
            ],
            [
                create_callback_button(
                    "💰 Business", "settings_profile_load_business"),
                create_callback_button(
                    "🎮 Casual", "settings_profile_load_casual")
            ],
            [
                create_callback_button("📋 Export Settings", "settings_export"),
                create_callback_button("📄 Import Settings", "settings_import")
            ],
            [
                create_callback_button("⬅️ Back to Settings", "settings_main")
            ]
        ]
    else:
        # Show main settings menu
        keyboard = [
            [
                create_callback_button("👤 Profile", "settings_profile"),
                create_callback_button("🎭 Roles", "settings_roles")
            ],
            [
                create_callback_button("💬 Chat", "settings_chat"),
                create_callback_button(
                    "🔔 Notifications", "settings_notifications")
            ],
            [
                create_callback_button("🔒 Privacy", "settings_privacy"),
                create_callback_button("🎛️ Advanced", "settings_advanced")
            ],
            [
                create_callback_button(
                    "📚 Settings Profiles", "settings_profiles")
            ],
            [
                create_callback_button("⬅️ Back to Menu", "menu_main")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


def create_memory_keyboard(show_categories: bool = False) -> InlineKeyboardMarkup:
    """
    Create the memory management keyboard.

    Args:
        show_categories: Whether to show the category selection view

    Returns:
        An InlineKeyboardMarkup instance with memory management buttons
    """
    if show_categories:
        # Show category selection view
        keyboard = [
            [
                create_callback_button(
                    "👤 Personal", "memory_category_personal"),
                create_callback_button(
                    "❤️ Preferences", "memory_category_preferences")
            ],
            [
                create_callback_button("🌐 Facts", "memory_category_facts"),
                create_callback_button("💼 Work", "memory_category_work")
            ],
            [
                create_callback_button(
                    "🌟 Interests", "memory_category_interests"),
                create_callback_button(
                    "👪 Relationships", "memory_category_relationships")
            ],
            [
                create_callback_button("🌍 Places", "memory_category_places"),
                create_callback_button("📅 Events", "memory_category_events")
            ],
            [
                create_callback_button(
                    "🎓 Education", "memory_category_education"),
                create_callback_button("🍔 Food", "memory_category_food")
            ],
            [
                create_callback_button("💰 Finance", "memory_category_finance"),
                create_callback_button("🎮 Hobbies", "memory_category_hobbies")
            ],
            [
                create_callback_button("📚 General", "memory_category_general")
            ],
            [
                create_callback_button("⬅️ Back to Memory Menu", "memory_main")
            ]
        ]
    else:
        # Show main memory management view
        keyboard = [
            [
                create_callback_button("📝 Add Memory", "memory_add"),
                create_callback_button("🔍 Search", "memory_search")
            ],
            [
                create_callback_button(
                    "📂 Browse Categories", "memory_categories"),
                create_callback_button("📊 Memory Map", "memory_map")
            ],
            [
                create_callback_button("📃 Recent Memories", "memory_recent"),
                create_callback_button(
                    "⭐ Important Memories", "memory_important")
            ],
            [
                create_callback_button("📋 Export Memories", "memory_export"),
                create_callback_button("📄 Import Memories", "memory_import")
            ],
            [
                create_callback_button("⬅️ Back to Menu", "menu_main")
            ]
        ]
    return InlineKeyboardMarkup(keyboard)


def create_memory_category_keyboard(category: str, has_memories: bool = True) -> InlineKeyboardMarkup:
    """
    Create a keyboard for a specific memory category.

    Args:
        category: The memory category
        has_memories: Whether the category has memories

    Returns:
        An InlineKeyboardMarkup instance with category-specific buttons
    """
    keyboard = []

    # Add memory management buttons
    keyboard.append([
        create_callback_button("📝 Add Memory", f"memory_add_to_{category}"),
        create_callback_button("🔍 Search", f"memory_search_in_{category}")
    ])

    # Add memory viewing options if there are memories
    if has_memories:
        keyboard.append([
            create_callback_button(
                "🔎 View All", f"memory_view_all_{category}"),
            create_callback_button(
                "⭐ By Importance", f"memory_importance_{category}")
        ])

        keyboard.append([
            create_callback_button("📆 By Date", f"memory_date_{category}"),
            create_callback_button("📋 Export", f"memory_export_{category}")
        ])

    # Add back button
    keyboard.append([
        create_callback_button("⬅️ Back to Categories", "memory_categories")
    ])

    return InlineKeyboardMarkup(keyboard)


def create_help_keyboard() -> InlineKeyboardMarkup:
    """
    Create the help menu keyboard.

    Returns:
        An InlineKeyboardMarkup instance with help category buttons
    """
    keyboard = [
        [
            create_callback_button("🔰 Basic Commands", "help_basic"),
            create_callback_button("🎭 Roleplay", "help_roleplay")
        ],
        [
            create_callback_button("🧠 Memory", "help_memory"),
            create_callback_button("⚙️ Settings", "help_settings")
        ],
        [
            create_callback_button("🔍 Advanced", "help_advanced")
        ],
        [
            create_callback_button("⬅️ Back to Menu", "menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def create_back_button(callback_data: str = "menu_main") -> InlineKeyboardMarkup:
    """
    Create a keyboard with just a back button.

    Args:
        callback_data: The callback data for the back button

    Returns:
        An InlineKeyboardMarkup instance with a back button
    """
    return InlineKeyboardMarkup([[
        create_callback_button("⬅️ Back", callback_data)
    ]])
