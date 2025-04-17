"""
Callback handlers for theme customization.
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.ui.buttons import create_callback_button
from jyra.ui.themes import get_theme, set_current_theme, ThemeType, THEMES
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_theme_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle theme-related callback queries.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user_id = update.effective_user.id

    if callback_data == "settings_theme" or callback_data.startswith("theme_category_"):
        # Show theme selection menu or category
        await show_theme_selection(update, context)

    elif callback_data.startswith("set_theme_"):
        # Set theme
        theme_name = callback_data[10:]  # Remove "set_theme_" prefix

        # Update user preference
        success = await User.update_user_preferences(user_id, {"theme": theme_name})

        if success:
            # Set current theme
            set_current_theme(theme_name)

            # Show confirmation
            theme = get_theme(theme_name)

            message = f"""
{bold("Theme Updated")} {theme.get_property("primary_emoji")}

Your theme has been set to {bold(theme_name.capitalize())}.

{italic("This theme will be applied to all your interactions with me.")}
"""

            # Create back buttons
            keyboard = [[
                create_callback_button(
                    "⬅️ Back to Themes", "settings_theme")
            ]]

            # Add preview button
            keyboard.append([
                create_callback_button(
                    "🔍 Preview Theme", f"preview_theme_{theme_name}")
            ])

            await query.message.edit_text(
                message,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        else:
            # Show error
            await query.message.edit_text(
                "Sorry, I couldn't update your theme. Please try again.",
                reply_markup=InlineKeyboardMarkup([[
                    create_callback_button(
                        "⬅️ Back to Settings", "settings_main")
                ]]),
                parse_mode='HTML'
            )

    elif callback_data.startswith("preview_theme_"):
        # Preview theme
        theme_name = callback_data[14:]  # Remove "preview_theme_" prefix
        theme = get_theme(theme_name)

        # Create a preview message using the theme's formatting
        primary_emoji = theme.get_property("primary_emoji")
        secondary_emoji = theme.get_property("secondary_emoji")
        section_prefix = theme.get_property("section_prefix")

        # Format a sample message using the theme's properties
        title = theme.format_title(f"Theme Preview: {theme_name.capitalize()}")
        description = theme.format_description(
            "This is how your messages will look with this theme.")

        # Create sample sections
        sections = [
            f"{section_prefix}This is a section with some content",
            f"{section_prefix}Buttons will have {theme.get_property('button_prefix')}this style{theme.get_property('button_suffix')}",
            f"{section_prefix}Emojis like {primary_emoji} and {secondary_emoji} will be used"
        ]

        # Format the preview message
        preview = f"{title}\n\n{description}\n\n" + "\n".join(sections)

        # Create back button
        keyboard = InlineKeyboardMarkup([[
            create_callback_button(
                "⬅️ Back", f"set_theme_{theme_name}")
        ]])

        await query.message.edit_text(
            preview,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    else:
        logger.warning(f"Unknown theme callback: {callback_data}")
        await query.message.edit_text(
            "Sorry, I don't recognize that theme option. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                create_callback_button("⬅️ Back to Settings", "settings_main")
            ]]),
            parse_mode='HTML'
        )


async def show_theme_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show the theme selection menu.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id

    # Get current theme preference
    preferences = await User.get_user_preferences(user_id)
    current_theme_name = preferences.get("theme", "default")

    # Check if we're showing a specific category
    category = None
    if query.data.startswith("theme_category_"):
        category = query.data[15:]  # Remove "theme_category_" prefix

    # Define theme categories
    theme_categories = {
        "basic": ["default", "light", "dark"],
        "colorful": ["colorful", "playful", "nature"],
        "professional": ["professional", "minimal", "elegant"],
        "special": ["tech", "retro"]
    }

    # If showing a specific category
    if category and category in theme_categories:
        # Create theme selection message for category
        message = f"""
{bold("Theme Settings")} 🎨

{bold(category.capitalize())} Themes

{bold("Current Theme:")} {current_theme_name.capitalize()}

{italic("Select a theme to customize how I look and feel.")}
"""

        # Create theme selection buttons for this category
        keyboard = []

        # Add theme buttons for this category
        for theme_name in theme_categories[category]:
            theme = THEMES.get(theme_name)
            if theme:
                emoji = theme.get_property("primary_emoji")
                button_text = f"{emoji} {theme_name.capitalize()}"

                if theme_name == current_theme_name:
                    button_text += " ✓"

                keyboard.append([
                    create_callback_button(
                        button_text, f"set_theme_{theme_name}")
                ])

        # Add navigation buttons
        keyboard.append([
            create_callback_button("⬅️ Back to Categories", "settings_theme")
        ])

    else:  # Show main theme categories
        # Create theme selection message
        message = f"""
{bold("Theme Settings")} 🎨

Select a theme category or choose from popular themes.

{bold("Current Theme:")} {current_theme_name.capitalize()}

{italic("Each theme changes the visual style of my messages and buttons.")}
"""

        # Create theme category buttons
        keyboard = [
            [
                create_callback_button("🔸 Basic", "theme_category_basic"),
                create_callback_button("🌈 Colorful", "theme_category_colorful")
            ],
            [
                create_callback_button(
                    "💼 Professional", "theme_category_professional"),
                create_callback_button("✨ Special", "theme_category_special")
            ]
        ]

        # Add popular themes section
        keyboard.append(
            [create_callback_button("🔝 Popular Themes", "_header")])

        # Add a few popular themes
        popular_themes = ["default", "dark", "colorful", "professional"]
        for theme_name in popular_themes:
            theme = THEMES.get(theme_name)
            if theme:
                emoji = theme.get_property("primary_emoji")
                button_text = f"{emoji} {theme_name.capitalize()}"

                if theme_name == current_theme_name:
                    button_text += " ✓"

                keyboard.append([
                    create_callback_button(
                        button_text, f"set_theme_{theme_name}")
                ])

        # Add back button
        keyboard.append([
            create_callback_button("⬅️ Back to Settings", "settings_main")
        ])

    # Filter out any header buttons (they're just for visual separation)
    keyboard = [row for row in keyboard if not any(
        btn.callback_data == "_header" for btn in row)]

    await query.message.edit_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
