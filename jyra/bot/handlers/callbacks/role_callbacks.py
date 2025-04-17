"""
Callback handlers for role selection and management.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from jyra.db.models.role import Role
from jyra.db.models.featured_refresh import refresh_featured_if_needed
from jyra.db.models.user import User
from jyra.ui.buttons import create_role_selection_keyboard, create_callback_button
from jyra.ui.messages import get_role_description
from jyra.ui.keyboards import create_main_menu_keyboard
from jyra.ui.formatting import bold, italic
from jyra.ui.visual_feedback import show_loading_indicator, stop_loading_indicator, show_success_message
from jyra.bot.handlers.commands.role_command import get_role_emoji
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def handle_roles_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the roles menu.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query

    user_id = update.effective_user.id

    # Refresh featured roles if needed (once per day)
    refresh_featured_if_needed()

    # Get available roles
    roles = await Role.get_all_roles(include_custom=True, created_by=user_id)

    if not roles:
        # Initialize default roles if none exist
        await Role.initialize_default_roles()
        roles = await Role.get_all_roles(include_custom=True, created_by=user_id)

    # Convert roles to list of dictionaries for the keyboard function
    role_dicts = []
    for role in roles:
        role_dict = {
            "role_id": role.role_id,
            "name": role.name,
            "emoji": get_role_emoji(role.name),
            "description": role.description,
            "is_custom": role.is_custom,
            "is_featured": getattr(role, 'is_featured', False),
            "is_popular": getattr(role, 'is_popular', False),
            "category": getattr(role, 'category', 'General')
        }
        role_dicts.append(role_dict)

    # Create role selection keyboard (default: all roles)
    keyboard = create_role_selection_keyboard(role_dicts)

    # Add category button
    keyboard.inline_keyboard.insert(0, [
        InlineKeyboardButton("📂 Browse by Category",
                             callback_data="roles_categories")
    ])

    # Add custom roles button if user has any
    custom_roles = [r for r in role_dicts if r["is_custom"]]
    if custom_roles:
        keyboard.inline_keyboard.insert(1, [
            InlineKeyboardButton("📝 My Custom Roles",
                                 callback_data="roles_filter_custom")
        ])

    await query.message.edit_text(
        "<b>Please select a roleplay persona for me:</b>\n\n"
        "🌟 = Featured   🔥 = Popular   📝 = Custom\n\nChoose a role below:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def show_role_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show role categories menu.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id

    # Get all roles to extract categories
    roles = await Role.get_all_roles(include_custom=True, created_by=user_id)

    # Extract unique categories
    categories = set()
    for role in roles:
        category = getattr(role, 'category', 'General')
        categories.add(category)

    # Define standard categories that should always be shown
    standard_categories = [
        "General", "Professional", "Creative", "Academic",
        "Entertainment", "Technical", "Personal", "Historical"
    ]

    # Ensure standard categories are included if they have roles
    for category in standard_categories:
        if any(getattr(role, 'category', 'General') == category for role in roles):
            categories.add(category)

    # Sort categories
    sorted_categories = sorted(list(categories))

    # Create category buttons
    keyboard = []
    for i in range(0, len(sorted_categories), 2):
        row = []
        row.append(InlineKeyboardButton(
            f"{sorted_categories[i]}",
            callback_data=f"roles_category_{sorted_categories[i]}"
        ))

        if i + 1 < len(sorted_categories):
            row.append(InlineKeyboardButton(
                f"{sorted_categories[i+1]}",
                callback_data=f"roles_category_{sorted_categories[i+1]}"
            ))

        keyboard.append(row)

    # Add filter buttons
    keyboard.append([
        InlineKeyboardButton(
            "🌟 Featured", callback_data="roles_filter_featured"),
        InlineKeyboardButton("🔥 Popular", callback_data="roles_filter_popular")
    ])

    # Add back button
    keyboard.append([
        InlineKeyboardButton("⬅️ Back to All Roles",
                             callback_data="roles_filter_all")
    ])

    await query.message.edit_text(
        "<b>Browse Roles by Category</b>\n\n"
        "Select a category to see roles:\n",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )


async def show_roles_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str) -> None:
    """
    Show roles filtered by category.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
        category (str): The category to filter by
    """
    query = update.callback_query
    user_id = update.effective_user.id

    # Get all roles
    roles = await Role.get_all_roles(include_custom=True, created_by=user_id)

    # Filter roles by category
    filtered_roles = []
    for role in roles:
        role_category = getattr(role, 'category', 'General')
        if role_category == category:
            role_dict = {
                "role_id": role.role_id,
                "name": role.name,
                "emoji": get_role_emoji(role.name),
                "description": role.description,
                "is_custom": role.is_custom,
                "is_featured": getattr(role, 'is_featured', False),
                "is_popular": getattr(role, 'is_popular', False),
                "category": role_category
            }
            filtered_roles.append(role_dict)

    if not filtered_roles:
        # No roles in this category
        await query.message.edit_text(
            f"<b>{category} Roles</b>\n\n"
            f"There are no roles in the {category} category yet.\n\n"
            "Try another category or create a custom role!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "⬅️ Back to Categories", callback_data="roles_categories")
            ]]),
            parse_mode='HTML'
        )
        return

    # Create keyboard with filtered roles
    keyboard = create_role_selection_keyboard(filtered_roles)

    # Add back button at the top
    keyboard.inline_keyboard.insert(0, [
        InlineKeyboardButton("⬅️ Back to Categories",
                             callback_data="roles_categories")
    ])

    await query.message.edit_text(
        f"<b>{category} Roles</b>\n\n"
        "Select a role from this category:\n",
        reply_markup=keyboard,
        parse_mode='HTML'
    )


async def handle_role_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle role-related callback queries.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user_id = update.effective_user.id

    # Handle role selection
    if callback_data.startswith("role_"):
        role_id = int(callback_data[5:])  # Remove "role_" prefix

        # Show loading indicator
        await show_loading_indicator(
            update, context, "Switching role", animation_type="dots"
        )

        try:
            # Get the selected role
            role = await Role.get_role(role_id)

            if not role:
                # Role not found
                logger.warning(f"Role not found: {role_id}")
                await stop_loading_indicator(context, False, "Role not found")
                await query.message.edit_text(
                    "Sorry, I couldn't find that role. Please try again.",
                    reply_markup=create_main_menu_keyboard()
                )
                return

            # Update user's current role
            user = await User.get_user(user_id)
            if user:
                user.current_role_id = role_id
                await user.save()

            # Stop loading indicator
            await stop_loading_indicator(context, True, "Role switched successfully")

            # Convert role to dictionary for the message function
            role_dict = {
                "name": role.name,
                "emoji": get_role_emoji(role.name),
                "description": role.description,
                "personality": role.personality,
                "speaking_style": role.speaking_style,
                "knowledge_areas": role.knowledge_areas,
                "behaviors": role.behaviors,
                "is_custom": role.is_custom,
                "created_by": role.created_by
            }

            # Get role description message
            role_text = get_role_description(role_dict)

            # Show full prompt engineering for this role
            prompt_engineering = f"<b>Prompt Engineering for {role.name}:</b>\n"
            prompt_engineering += f"<b>Personality:</b> {role.personality or 'N/A'}\n"
            prompt_engineering += f"<b>Speaking Style:</b> {role.speaking_style or 'N/A'}\n"
            prompt_engineering += f"<b>Knowledge Areas:</b> {role.knowledge_areas or 'N/A'}\n"
            prompt_engineering += f"<b>Behaviors:</b> {role.behaviors or 'N/A'}\n"

            # Create main menu keyboard
            keyboard = create_main_menu_keyboard()

            # Show success message with role information
            await query.message.edit_text(
                f"{role_text}\n\n{prompt_engineering}\n<b>I'm now in {role.name} mode!</b> {get_role_emoji(role.name)}\nHow can I assist you today?",
                reply_markup=keyboard,
                parse_mode='HTML'
            )

        except Exception as e:
            # Handle errors
            logger.error(f"Error switching role: {str(e)}")
            await stop_loading_indicator(context, False, "Error switching role")
            await query.message.edit_text(
                "Sorry, I encountered an error while switching roles. Please try again.",
                reply_markup=create_main_menu_keyboard()
            )

    # Handle role pagination
    elif callback_data.startswith("roles_page_"):
        page = int(callback_data[11:])  # Remove "roles_page_" prefix

        # Get available roles
        roles = await Role.get_all_roles(include_custom=True, created_by=user_id)

        # Convert roles to list of dictionaries
        role_dicts = []
        for role in roles:
            role_dict = {
                "role_id": role.role_id,
                "name": role.name,
                "emoji": get_role_emoji(role.name),
                "description": role.description,
                "is_custom": role.is_custom,
                "is_featured": getattr(role, 'is_featured', False),
                "is_popular": getattr(role, 'is_popular', False)
            }
            role_dicts.append(role_dict)

        # Create role selection keyboard for the specified page
        keyboard = create_role_selection_keyboard(role_dicts, page=page)

        await query.message.edit_text(
            "<b>Please select a roleplay persona for me:</b>\n\n"
            "🌟 = Featured   🔥 = Popular\n\nChoose a role below:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    # Handle role filter buttons
    elif callback_data in ("roles_filter_featured", "roles_filter_popular", "roles_filter_all", "roles_filter_custom"):
        # Get available roles
        roles = await Role.get_all_roles(include_custom=True, created_by=user_id)
        role_dicts = []
        for role in roles:
            role_dict = {
                "role_id": role.role_id,
                "name": role.name,
                "emoji": get_role_emoji(role.name),
                "description": role.description,
                "is_custom": role.is_custom,
                "is_featured": getattr(role, 'is_featured', False),
                "is_popular": getattr(role, 'is_popular', False),
                "category": getattr(role, 'category', 'General')
            }
            role_dicts.append(role_dict)

        # Set filter type based on callback data
        if callback_data == "roles_filter_featured":
            filter_type = 'featured'
            title = "Featured Roles"
        elif callback_data == "roles_filter_popular":
            filter_type = 'popular'
            title = "Popular Roles"
        elif callback_data == "roles_filter_custom":
            filter_type = 'custom'
            title = "Your Custom Roles"
        else:
            filter_type = None
            title = "All Roles"

        keyboard = create_role_selection_keyboard(
            role_dicts, filter_type=filter_type)

        await query.message.edit_text(
            f"<b>{title}</b>\n\n"
            "🌟 = Featured   🔥 = Popular   📝 = Custom\n\nChoose a role below:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return

    # Handle role categories
    elif callback_data == "roles_categories":
        # Show role categories menu
        await show_role_categories(update, context)
        return

    # Handle specific role category
    elif callback_data.startswith("roles_category_"):
        category = callback_data[15:]  # Remove "roles_category_" prefix
        await show_roles_by_category(update, context, category)
        return

    # Handle create role button
    elif callback_data == "create_role":
        # Redirect to create_role_command
        await query.message.edit_text(
            "Let's create a custom roleplay persona!\n\n"
            "Please use the /createrole command to start the creation process."
        )

    else:
        logger.warning(f"Unknown role callback: {callback_data}")
        await query.message.edit_text(
            "Sorry, I don't recognize that option. Please try again.",
            reply_markup=create_main_menu_keyboard()
        )
        return
