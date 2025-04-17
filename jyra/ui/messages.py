"""
Message templates for Jyra bot.

This module provides functions for creating consistent message templates
throughout the bot interface.
"""

from typing import Dict, Any, Optional, List
from jyra.ui.formatting import bold, italic, code, emoji_prefix, create_section

# Message templates
WELCOME_MESSAGE = """
{greeting} {name}! {emoji}

I'm Jyra, your emotionally intelligent AI companion. {is_new_user_text}

{prompt}
"""

HELP_MESSAGE = """
{title}

{content}

{prompt}
"""

ROLE_DESCRIPTION = """
{name} {emoji}

{description}

{details}

{prompt}
"""

SETTINGS_MESSAGE = """
{title}

{content}

{prompt}
"""

MEMORY_MESSAGE = """
{title}

{content}

{prompt}
"""

ERROR_MESSAGE = """
{emoji} {message}

{details}
"""


def format_message(template: str, **kwargs) -> str:
    """
    Format a message template with the given parameters.

    Args:
        template: The message template
        **kwargs: Parameters to format the template with

    Returns:
        The formatted message
    """
    return template.format(**kwargs)


def get_welcome_message(name: str, is_new_user: bool = True) -> str:
    """
    Get a formatted welcome message.

    Args:
        name: The user's name
        is_new_user: Whether this is a new user

    Returns:
        A formatted welcome message
    """
    if is_new_user:
        greeting = "Welcome"
        emoji = "🌟"
        is_new_user_text = "I'm designed to remember you and adapt to your needs."
        prompt = "Let's get started on our journey together! Use the buttons below to navigate or just start chatting."
    else:
        greeting = "Welcome back"
        emoji = "✨"
        is_new_user_text = "It's great to see you again."
        prompt = "How can I assist you today? Use the buttons below or just start chatting."

    return format_message(
        WELCOME_MESSAGE,
        greeting=bold(greeting),
        name=name,
        emoji=emoji,
        is_new_user_text=is_new_user_text,
        prompt=prompt
    )


def get_help_message(category: str = "main") -> str:
    """
    Get a formatted help message for the given category.

    Args:
        category: The help category

    Returns:
        A formatted help message
    """
    title = bold("Jyra Help Center") + " ❓"

    if category == "main":
        content = "Select a category to learn more about Jyra's features."
        prompt = "Use the buttons below to explore different help categories."
    elif category == "basic":
        content = create_section("Basic Commands", [
            emoji_prefix("🚀", bold("/start") +
                         " - Begin your journey with Jyra"),
            emoji_prefix("❓", bold("/help") +
                         " - Display available commands and features"),
            emoji_prefix("ℹ️", bold("/about") + " - Learn more about Jyra"),
            emoji_prefix("⚙️", bold("/settings") +
                         " - Adjust your preferences")
        ])
        prompt = "Select another category or go back to the main menu."
    elif category == "roleplay":
        content = create_section("Roleplay Features", [
            emoji_prefix("🎭", bold("/role") +
                         " - Choose a roleplay persona for Jyra"),
            emoji_prefix("🔄", bold("/switchrole") +
                         " - Change to a different persona"),
            emoji_prefix("✏️", bold("/createrole") +
                         " - Create your own custom persona")
        ])
        prompt = "Select another category or go back to the main menu."
    elif category == "memory":
        content = create_section("Memory Features", [
            emoji_prefix("📝", bold("/remember") +
                         " - Tell Jyra something to remember"),
            emoji_prefix("🗑️", bold("/forget") +
                         " - Ask Jyra to forget a memory"),
            emoji_prefix("🧠", "Jyra automatically remembers important details")
        ])
        prompt = "Select another category or go back to the main menu."
    elif category == "settings":
        content = create_section("Settings", [
            emoji_prefix("👤", "Profile settings"),
            emoji_prefix("🎭", "Role preferences"),
            emoji_prefix("💬", "Chat settings"),
            emoji_prefix("🔔", "Notifications"),
            emoji_prefix("🔒", "Privacy settings")
        ])
        prompt = "Select another category or go back to the main menu."
    elif category == "advanced":
        content = create_section("Advanced Features", [
            emoji_prefix("📊", bold("/mood") +
                         " - Check your emotional trends"),
            emoji_prefix("🔊", bold("/voice") + " - Toggle voice responses"),
            emoji_prefix("🖼️", "Send images for Jyra to analyze"),
            emoji_prefix("🎤", "Send voice messages for Jyra to respond to")
        ])
        prompt = "Select another category or go back to the main menu."
    else:
        content = "Unknown help category."
        prompt = "Please select a valid category."

    return format_message(
        HELP_MESSAGE,
        title=title,
        content=content,
        prompt=prompt
    )


def get_role_description(role: Dict[str, Any]) -> str:
    """
    Get a formatted role description.

    Args:
        role: The role dictionary

    Returns:
        A formatted role description
    """
    name = bold(role.get("name", "Unknown Role"))
    emoji = role.get("emoji", "")
    description = role.get("description", "No description available.")

    details_items = []
    if role.get("personality"):
        details_items.append(emoji_prefix(
            "👤", bold("Personality: ") + role["personality"]))
    if role.get("speaking_style"):
        details_items.append(emoji_prefix(
            "💬", bold("Speaking Style: ") + role["speaking_style"]))
    if role.get("knowledge_areas"):
        details_items.append(emoji_prefix(
            "🧠", bold("Knowledge Areas: ") + role["knowledge_areas"]))
    if role.get("behaviors"):
        details_items.append(emoji_prefix(
            "🔄", bold("Behaviors: ") + role["behaviors"]))

    details = "\n\n".join(details_items) if details_items else ""

    if role.get("is_custom") and role.get("created_by"):
        created_by = f"\nCreated by: {role['created_by']}"
    else:
        created_by = ""

    prompt = "Use the buttons below to select this role or explore others."

    return format_message(
        ROLE_DESCRIPTION,
        name=name,
        emoji=emoji,
        description=description,
        details=details + created_by,
        prompt=prompt
    )


def get_settings_message(category: str = "main") -> str:
    """
    Get a formatted settings message for the given category.

    Args:
        category: The settings category

    Returns:
        A formatted settings message
    """
    title = bold("Jyra Settings") + " ⚙️"

    if category == "main":
        content = "Select a category to adjust your settings."
        prompt = "Use the buttons below to navigate settings categories."
    elif category == "profile":
        content = create_section("Profile Settings", [
            emoji_prefix("👤", "Update your profile information"),
            emoji_prefix("🌐", "Change language preferences"),
            emoji_prefix("🎨", "Customize appearance")
        ])
        prompt = "Select a setting to modify or go back to the main settings."
    elif category == "roles":
        content = create_section("Role Settings", [
            emoji_prefix("🎭", "Manage custom roles"),
            emoji_prefix("⭐", "Set favorite roles"),
            emoji_prefix("🔄", "Configure role switching behavior")
        ])
        prompt = "Select a setting to modify or go back to the main settings."
    elif category == "chat":
        content = create_section("Chat Settings", [
            emoji_prefix("💬", "Adjust message formatting"),
            emoji_prefix("📏", "Set response length preference"),
            emoji_prefix("👔", "Set formality level"),
            emoji_prefix("🎨", "Choose theme")
        ])
        prompt = "Select a setting to modify or go back to the main settings."
    elif category == "advanced":
        content = create_section("Advanced Settings", [
            emoji_prefix("🧠", "AI model settings"),
            emoji_prefix("🔄", "Context window size"),
            emoji_prefix("⚡", "Performance options"),
            emoji_prefix("🔌", "API integrations")
        ])
        prompt = "Select a setting to modify or go back to the main settings."
    elif category == "privacy":
        content = create_section("Privacy Settings", [
            emoji_prefix("🔒", "Data retention"),
            emoji_prefix("👁️", "Visibility controls"),
            emoji_prefix("🗑️", "Data deletion options"),
            emoji_prefix("📊", "Analytics preferences")
        ])
        prompt = "Select a setting to modify or go back to the main settings."
    elif category == "notifications":
        content = create_section("Notification Settings", [
            emoji_prefix("🔔", "Enable/disable notifications"),
            emoji_prefix("⏰", "Reminder frequency"),
            emoji_prefix("📱", "Notification channels"),
            emoji_prefix("🔕", "Quiet hours")
        ])
        prompt = "Select a setting to modify or go back to the main settings."
    elif category == "profiles":
        content = create_section("Settings Profiles", [
            emoji_prefix("💾", "Save your current settings as a profile"),
            emoji_prefix("📂", "Load a predefined or custom profile"),
            emoji_prefix("📤", "Export your settings"),
            emoji_prefix("📥", "Import settings")
        ])
        prompt = "Settings profiles allow you to quickly switch between different configurations."
    else:
        content = "Unknown settings category."
        prompt = "Please select a valid category."

    return format_message(
        SETTINGS_MESSAGE,
        title=title,
        content=content,
        prompt=prompt
    )


def get_error_message(message: str, details: str = "") -> str:
    """
    Get a formatted error message.

    Args:
        message: The error message
        details: Additional error details

    Returns:
        A formatted error message
    """
    return format_message(
        ERROR_MESSAGE,
        emoji="❌",
        message=bold(message),
        details=details
    )
