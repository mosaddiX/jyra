"""
Theme system for Jyra bot.

This module provides a theme system for customizing the visual appearance
of the bot's messages and UI elements.
"""

from typing import Dict, Any, Optional, List
from enum import Enum, auto

from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


class ThemeType(Enum):
    """Enum for theme types."""
    DEFAULT = auto()
    LIGHT = auto()
    DARK = auto()
    COLORFUL = auto()
    MINIMAL = auto()
    PROFESSIONAL = auto()
    PLAYFUL = auto()
    NATURE = auto()
    TECH = auto()
    ELEGANT = auto()
    RETRO = auto()

# Define theme properties


class Theme:
    """
    Theme class for customizing the visual appearance of the bot.
    """

    def __init__(self, theme_type: ThemeType = ThemeType.DEFAULT):
        """
        Initialize a theme.

        Args:
            theme_type: The theme type
        """
        self.theme_type = theme_type
        self.properties = self._get_theme_properties(theme_type)

    def _get_theme_properties(self, theme_type: ThemeType) -> Dict[str, Any]:
        """
        Get the properties for a theme type.

        Args:
            theme_type: The theme type

        Returns:
            A dictionary of theme properties
        """
        # Default theme properties
        default_properties = {
            "primary_emoji": "🌟",
            "secondary_emoji": "✨",
            "success_emoji": "✅",
            "error_emoji": "❌",
            "warning_emoji": "⚠️",
            "info_emoji": "ℹ️",
            "section_prefix": "• ",
            "button_prefix": "",
            "button_suffix": "",
            "title_prefix": "",
            "title_suffix": "",
            "use_bold_titles": True,
            "use_italic_descriptions": True,
            "use_emojis": True,
            "use_separators": True,
            "separator": "\n\n",
            "list_style": "• ",
            "ordered_list_style": "number",  # "number" or "letter"
            "quote_style": "> ",
            "code_style": "inline",  # "inline" or "block"
            "link_style": "inline",  # "inline" or "button"
            "message_style": "normal",  # "normal" or "compact"
            "color_scheme": {
                "primary": "#3498db",
                "secondary": "#2ecc71",
                "accent": "#e74c3c",
                "background": "#ffffff",
                "text": "#333333"
            }
        }

        # Theme-specific properties
        if theme_type == ThemeType.LIGHT:
            return {
                **default_properties,
                "primary_emoji": "☀️",
                "secondary_emoji": "🌤️",
                "section_prefix": "◉ ",
                "color_scheme": {
                    "primary": "#4a90e2",
                    "secondary": "#50c878",
                    "accent": "#ff6b6b",
                    "background": "#f8f9fa",
                    "text": "#212529"
                }
            }

        elif theme_type == ThemeType.DARK:
            return {
                **default_properties,
                "primary_emoji": "🌙",
                "secondary_emoji": "✨",
                "section_prefix": "◆ ",
                "color_scheme": {
                    "primary": "#61afef",
                    "secondary": "#98c379",
                    "accent": "#e06c75",
                    "background": "#282c34",
                    "text": "#abb2bf"
                }
            }

        elif theme_type == ThemeType.COLORFUL:
            return {
                **default_properties,
                "primary_emoji": "🌈",
                "secondary_emoji": "🎨",
                "section_prefix": "★ ",
                "button_prefix": "【 ",
                "button_suffix": " 】",
                "use_separators": True,
                "separator": "\n━━━━━━━━━━━━━━━━━━\n",
                "color_scheme": {
                    "primary": "#ff7eb9",
                    "secondary": "#7afcff",
                    "accent": "#feff9c",
                    "background": "#fff740",
                    "text": "#6eb5ff"
                }
            }

        elif theme_type == ThemeType.MINIMAL:
            return {
                **default_properties,
                "primary_emoji": "◯",
                "secondary_emoji": "◯",
                "success_emoji": "✓",
                "error_emoji": "✗",
                "warning_emoji": "!",
                "info_emoji": "i",
                "section_prefix": "",
                "button_prefix": "",
                "button_suffix": "",
                "use_bold_titles": True,
                "use_italic_descriptions": False,
                "use_emojis": False,
                "use_separators": False,
                "separator": "\n",
                "list_style": "- ",
                "color_scheme": {
                    "primary": "#000000",
                    "secondary": "#666666",
                    "accent": "#999999",
                    "background": "#ffffff",
                    "text": "#333333"
                }
            }

        elif theme_type == ThemeType.PROFESSIONAL:
            return {
                **default_properties,
                "primary_emoji": "📊",
                "secondary_emoji": "📈",
                "section_prefix": "■ ",
                "use_bold_titles": True,
                "use_italic_descriptions": False,
                "use_separators": True,
                "separator": "\n\n",
                "list_style": "• ",
                "color_scheme": {
                    "primary": "#0073b1",
                    "secondary": "#006097",
                    "accent": "#f5ae42",
                    "background": "#f3f6f8",
                    "text": "#333333"
                }
            }

        elif theme_type == ThemeType.PLAYFUL:
            return {
                **default_properties,
                "primary_emoji": "🎮",
                "secondary_emoji": "🎯",
                "section_prefix": "🔹 ",
                "button_prefix": "🎲 ",
                "button_suffix": " 🎲",
                "title_prefix": "✨ ",
                "title_suffix": " ✨",
                "use_bold_titles": True,
                "use_italic_descriptions": True,
                "use_emojis": True,
                "use_separators": True,
                "separator": "\n🎮 🎮 🎮 🎮 🎮 🎮 🎮\n",
                "color_scheme": {
                    "primary": "#ff3366",
                    "secondary": "#33ccff",
                    "accent": "#ffcc33",
                    "background": "#6633ff",
                    "text": "#ffffff"
                }
            }

        elif theme_type == ThemeType.NATURE:
            return {
                **default_properties,
                "primary_emoji": "🌿",
                "secondary_emoji": "🌳",
                "success_emoji": "🌼",
                "error_emoji": "🍃",
                "warning_emoji": "🍁",
                "info_emoji": "🌺",
                "section_prefix": "🍀 ",
                "button_prefix": "🌸 ",
                "button_suffix": " 🌸",
                "title_prefix": "🌴 ",
                "title_suffix": " 🌴",
                "use_bold_titles": True,
                "use_italic_descriptions": True,
                "use_emojis": True,
                "use_separators": True,
                "separator": "\n🌼 🌺 🌼 🌺 🌼\n",
                "list_style": "🍂 ",
                "color_scheme": {
                    "primary": "#4caf50",
                    "secondary": "#8bc34a",
                    "accent": "#ff9800",
                    "background": "#e8f5e9",
                    "text": "#33691e"
                }
            }

        elif theme_type == ThemeType.TECH:
            return {
                **default_properties,
                "primary_emoji": "💻",
                "secondary_emoji": "📱",
                "success_emoji": "✅",
                "error_emoji": "❌",
                "warning_emoji": "⚠️",
                "info_emoji": "💬",
                "section_prefix": "🔸 ",
                "button_prefix": "[ ",
                "button_suffix": " ]",
                "title_prefix": "// ",
                "title_suffix": "",
                "use_bold_titles": True,
                "use_italic_descriptions": False,
                "use_emojis": True,
                "use_separators": True,
                "separator": "\n/* -------------------------------- */\n",
                "list_style": "$ ",
                "color_scheme": {
                    "primary": "#00bcd4",
                    "secondary": "#607d8b",
                    "accent": "#ff5722",
                    "background": "#263238",
                    "text": "#eceff1"
                }
            }

        elif theme_type == ThemeType.ELEGANT:
            return {
                **default_properties,
                "primary_emoji": "💎",
                "secondary_emoji": "✨",
                "success_emoji": "✅",
                "error_emoji": "❌",
                "warning_emoji": "⚠️",
                "info_emoji": "ℹ️",
                "section_prefix": "• ",
                "button_prefix": "",
                "button_suffix": "",
                "title_prefix": "",
                "title_suffix": "",
                "use_bold_titles": True,
                "use_italic_descriptions": True,
                "use_emojis": True,
                "use_separators": True,
                "separator": "\n\n",
                "list_style": "• ",
                "color_scheme": {
                    "primary": "#9c27b0",
                    "secondary": "#7b1fa2",
                    "accent": "#e91e63",
                    "background": "#f3e5f5",
                    "text": "#4a148c"
                }
            }

        elif theme_type == ThemeType.RETRO:
            return {
                **default_properties,
                "primary_emoji": "🎵",
                "secondary_emoji": "🎧",
                "success_emoji": "👍",
                "error_emoji": "👎",
                "warning_emoji": "🔔",
                "info_emoji": "💿",
                "section_prefix": ">> ",
                "button_prefix": "<< ",
                "button_suffix": " >>",
                "title_prefix": ":: ",
                "title_suffix": " ::",
                "use_bold_titles": True,
                "use_italic_descriptions": False,
                "use_emojis": True,
                "use_separators": True,
                "separator": "\n==================\n",
                "list_style": "* ",
                "color_scheme": {
                    "primary": "#ff4081",
                    "secondary": "#536dfe",
                    "accent": "#ffeb3b",
                    "background": "#212121",
                    "text": "#ffffff"
                }
            }

        # Default theme
        return default_properties

    def get_property(self, property_name: str) -> Any:
        """
        Get a theme property.

        Args:
            property_name: The property name

        Returns:
            The property value
        """
        return self.properties.get(property_name)

    def format_title(self, title: str) -> str:
        """
        Format a title according to the theme.

        Args:
            title: The title text

        Returns:
            The formatted title
        """
        prefix = self.get_property("title_prefix")
        suffix = self.get_property("title_suffix")
        use_bold = self.get_property("use_bold_titles")

        formatted_title = f"{prefix}{title}{suffix}"

        if use_bold:
            return f"<b>{formatted_title}</b>"

        return formatted_title

    def format_description(self, description: str) -> str:
        """
        Format a description according to the theme.

        Args:
            description: The description text

        Returns:
            The formatted description
        """
        use_italic = self.get_property("use_italic_descriptions")

        if use_italic:
            return f"<i>{description}</i>"

        return description

    def format_section(self, title: str, items: List[str]) -> str:
        """
        Format a section according to the theme.

        Args:
            title: The section title
            items: The section items

        Returns:
            The formatted section
        """
        formatted_title = self.format_title(title)
        section_prefix = self.get_property("section_prefix")
        list_style = self.get_property("list_style")
        separator = self.get_property("separator")

        formatted_items = []
        for item in items:
            if section_prefix and not item.startswith(section_prefix):
                formatted_items.append(f"{section_prefix}{item}")
            else:
                formatted_items.append(item)

        return f"{formatted_title}{separator}{separator.join(formatted_items)}"

    def format_button_text(self, text: str) -> str:
        """
        Format button text according to the theme.

        Args:
            text: The button text

        Returns:
            The formatted button text
        """
        prefix = self.get_property("button_prefix")
        suffix = self.get_property("button_suffix")

        return f"{prefix}{text}{suffix}"

    def format_list_item(self, item: str, index: Optional[int] = None) -> str:
        """
        Format a list item according to the theme.

        Args:
            item: The list item text
            index: Optional index for ordered lists

        Returns:
            The formatted list item
        """
        list_style = self.get_property("list_style")
        ordered_list_style = self.get_property("ordered_list_style")

        if index is not None:
            if ordered_list_style == "number":
                return f"{index + 1}. {item}"
            elif ordered_list_style == "letter":
                return f"{chr(97 + index)}. {item}"

        return f"{list_style}{item}"

    def format_message(self, message: str) -> str:
        """
        Format a message according to the theme.

        Args:
            message: The message text

        Returns:
            The formatted message
        """
        message_style = self.get_property("message_style")

        if message_style == "compact":
            # Remove extra whitespace
            lines = [line.strip() for line in message.split("\n")]
            return "\n".join([line for line in lines if line])

        return message


# Create theme instances
DEFAULT_THEME = Theme(ThemeType.DEFAULT)
LIGHT_THEME = Theme(ThemeType.LIGHT)
DARK_THEME = Theme(ThemeType.DARK)
COLORFUL_THEME = Theme(ThemeType.COLORFUL)
MINIMAL_THEME = Theme(ThemeType.MINIMAL)
PROFESSIONAL_THEME = Theme(ThemeType.PROFESSIONAL)
PLAYFUL_THEME = Theme(ThemeType.PLAYFUL)
NATURE_THEME = Theme(ThemeType.NATURE)
TECH_THEME = Theme(ThemeType.TECH)
ELEGANT_THEME = Theme(ThemeType.ELEGANT)
RETRO_THEME = Theme(ThemeType.RETRO)

# Theme registry
THEMES = {
    "default": DEFAULT_THEME,
    "light": LIGHT_THEME,
    "dark": DARK_THEME,
    "colorful": COLORFUL_THEME,
    "minimal": MINIMAL_THEME,
    "professional": PROFESSIONAL_THEME,
    "playful": PLAYFUL_THEME,
    "nature": NATURE_THEME,
    "tech": TECH_THEME,
    "elegant": ELEGANT_THEME,
    "retro": RETRO_THEME
}

# Current theme (default to DEFAULT)
current_theme = DEFAULT_THEME


def get_theme(theme_name: str = "default") -> Theme:
    """
    Get a theme by name.

    Args:
        theme_name: The theme name

    Returns:
        The theme instance
    """
    return THEMES.get(theme_name.lower(), DEFAULT_THEME)


def set_current_theme(theme_name: str) -> None:
    """
    Set the current theme.

    Args:
        theme_name: The theme name
    """
    global current_theme
    current_theme = get_theme(theme_name)


def get_current_theme() -> Theme:
    """
    Get the current theme.

    Returns:
        The current theme instance
    """
    return current_theme
