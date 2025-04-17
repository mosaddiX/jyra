"""
Text formatting utilities for Jyra bot.

This module provides functions for consistent text formatting
throughout the bot interface.
"""

from typing import List, Optional

def bold(text: str) -> str:
    """
    Format text as bold.
    
    Args:
        text: The text to format
        
    Returns:
        The formatted text
    """
    return f"<b>{text}</b>"

def italic(text: str) -> str:
    """
    Format text as italic.
    
    Args:
        text: The text to format
        
    Returns:
        The formatted text
    """
    return f"<i>{text}</i>"

def code(text: str) -> str:
    """
    Format text as inline code.
    
    Args:
        text: The text to format
        
    Returns:
        The formatted text
    """
    return f"<code>{text}</code>"

def pre(text: str) -> str:
    """
    Format text as a preformatted block.
    
    Args:
        text: The text to format
        
    Returns:
        The formatted text
    """
    return f"<pre>{text}</pre>"

def link(text: str, url: str) -> str:
    """
    Format text as a hyperlink.
    
    Args:
        text: The link text
        url: The URL
        
    Returns:
        The formatted link
    """
    return f'<a href="{url}">{text}</a>'

def emoji_prefix(emoji: str, text: str) -> str:
    """
    Add an emoji prefix to text.
    
    Args:
        emoji: The emoji to use as prefix
        text: The text to prefix
        
    Returns:
        The text with emoji prefix
    """
    return f"{emoji} {text}"

def format_list(items: List[str], ordered: bool = False) -> str:
    """
    Format a list of items.
    
    Args:
        items: The list items
        ordered: Whether to create an ordered list
        
    Returns:
        The formatted list
    """
    if not items:
        return ""
    
    result = []
    for i, item in enumerate(items):
        if ordered:
            result.append(f"{i+1}. {item}")
        else:
            result.append(f"• {item}")
    
    return "\n".join(result)

def create_section(title: str, content: List[str]) -> str:
    """
    Create a formatted section with title and content.
    
    Args:
        title: The section title
        content: The section content as a list of strings
        
    Returns:
        The formatted section
    """
    if isinstance(content, list):
        content_text = "\n".join(content)
    else:
        content_text = content
    
    return f"{bold(title)}\n\n{content_text}"
