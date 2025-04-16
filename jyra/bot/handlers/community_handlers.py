"""
Community engagement handlers for Jyra Telegram bot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from jyra.community.feedback import Feedback
from jyra.community.feature_requests import FeatureRequest
from jyra.community.support import SupportTicket
from jyra.db.models.user import User
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

# Conversation states
(
    FEEDBACK_TYPE,
    FEEDBACK_CONTENT,
    FEEDBACK_RATING,
    FEATURE_TITLE,
    FEATURE_DESCRIPTION,
    SUPPORT_SUBJECT,
    SUPPORT_DESCRIPTION,
    SUPPORT_PRIORITY,
) = range(8)


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /feedback command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    user_id = update.effective_user.id

    # Set conversation state
    context.user_data["providing_feedback"] = True

    # Create keyboard with feedback types
    keyboard = [
        [InlineKeyboardButton("🐛 Bug Report", callback_data="feedback_bug")],
        [InlineKeyboardButton("💡 Feature Suggestion",
                              callback_data="feedback_feature")],
        [InlineKeyboardButton("📝 General Feedback",
                              callback_data="feedback_general")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_feedback")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Thank you for providing feedback! What type of feedback would you like to share?",
        reply_markup=reply_markup
    )

    return FEEDBACK_TYPE


async def feedback_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle feedback type selection.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    query = update.callback_query
    await query.answer()

    feedback_type = query.data.replace("feedback_", "")
    context.user_data["feedback_type"] = feedback_type

    type_labels = {
        "bug": "Bug Report",
        "feature": "Feature Suggestion",
        "general": "General Feedback"
    }

    await query.edit_message_text(
        f"You selected: {type_labels[feedback_type]}\n\n"
        f"Please describe your {type_labels[feedback_type]} in detail:"
    )

    return FEEDBACK_CONTENT


async def feedback_content(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle feedback content.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    user_id = update.effective_user.id
    feedback_content = update.message.text

    context.user_data["feedback_content"] = feedback_content

    # For bug reports and feature suggestions, we're done
    if context.user_data["feedback_type"] in ["bug", "feature"]:
        # Save feedback
        await Feedback.add_feedback(
            user_id=user_id,
            feedback_type=context.user_data["feedback_type"],
            content=feedback_content,
            rating=0
        )

        # If it's a feature suggestion, also create a feature request
        if context.user_data["feedback_type"] == "feature":
            # Extract a title from the first line or first few words
            lines = feedback_content.strip().split('\n')
            title = lines[0][:50] if lines else feedback_content[:50]
            if len(title) == 50:
                title += "..."

            await FeatureRequest.add_feature_request(
                user_id=user_id,
                title=title,
                description=feedback_content
            )

        await update.message.reply_text(
            "Thank you for your feedback! It has been recorded and will be reviewed by our team."
        )

        # Clear conversation state
        context.user_data["providing_feedback"] = False
        context.user_data.pop("feedback_type", None)
        context.user_data.pop("feedback_content", None)

        return ConversationHandler.END

    # For general feedback, ask for a rating
    keyboard = [
        [
            InlineKeyboardButton("1 ⭐", callback_data="rating_1"),
            InlineKeyboardButton("2 ⭐", callback_data="rating_2"),
            InlineKeyboardButton("3 ⭐", callback_data="rating_3"),
            InlineKeyboardButton("4 ⭐", callback_data="rating_4"),
            InlineKeyboardButton("5 ⭐", callback_data="rating_5")
        ],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_feedback")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Thank you for your feedback! How would you rate your experience with Jyra?",
        reply_markup=reply_markup
    )

    return FEEDBACK_RATING


async def feedback_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle feedback rating selection.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    rating = int(query.data.replace("rating_", ""))

    # Save feedback with rating
    await Feedback.add_feedback(
        user_id=user_id,
        feedback_type=context.user_data["feedback_type"],
        content=context.user_data["feedback_content"],
        rating=rating
    )

    await query.edit_message_text(
        f"Thank you for your feedback and {rating}-star rating! "
        f"Your input helps us improve Jyra."
    )

    # Clear conversation state
    context.user_data["providing_feedback"] = False
    context.user_data.pop("feedback_type", None)
    context.user_data.pop("feedback_content", None)

    return ConversationHandler.END


async def feature_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /feature command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    user_id = update.effective_user.id

    # Set conversation state
    context.user_data["requesting_feature"] = True

    await update.message.reply_text(
        "Thank you for suggesting a feature! Please provide a title for your feature request:"
    )

    return FEATURE_TITLE


async def feature_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle feature request title.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    feature_title = update.message.text

    context.user_data["feature_title"] = feature_title

    await update.message.reply_text(
        f"Title: {feature_title}\n\n"
        f"Now, please describe the feature in detail. Include what problem it solves and how you envision it working:"
    )

    return FEATURE_DESCRIPTION


async def feature_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle feature request description.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    user_id = update.effective_user.id
    feature_description = update.message.text

    # Save feature request
    request_id = await FeatureRequest.add_feature_request(
        user_id=user_id,
        title=context.user_data["feature_title"],
        description=feature_description
    )

    if request_id:
        # Also vote for the feature
        await FeatureRequest.vote_for_feature(request_id, user_id)

        await update.message.reply_text(
            "Thank you for your feature request! It has been recorded and will be reviewed by our team.\n\n"
            "Your request has automatically received your vote. The more votes a feature gets, the more likely it is to be implemented."
        )
    else:
        await update.message.reply_text(
            "There was an error submitting your feature request. Please try again later."
        )

    # Clear conversation state
    context.user_data["requesting_feature"] = False
    context.user_data.pop("feature_title", None)

    return ConversationHandler.END


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle the /support command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    user_id = update.effective_user.id

    # Set conversation state
    context.user_data["creating_ticket"] = True

    await update.message.reply_text(
        "Need help? Let's create a support ticket. Please provide a subject for your ticket:"
    )

    return SUPPORT_SUBJECT


async def support_subject(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle support ticket subject.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    support_subject = update.message.text

    context.user_data["support_subject"] = support_subject

    await update.message.reply_text(
        f"Subject: {support_subject}\n\n"
        f"Now, please describe your issue in detail:"
    )

    return SUPPORT_DESCRIPTION


async def support_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle support ticket description.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    support_description = update.message.text

    context.user_data["support_description"] = support_description

    # Create keyboard with priority options
    keyboard = [
        [InlineKeyboardButton("🟢 Low", callback_data="priority_low")],
        [InlineKeyboardButton("🟡 Medium", callback_data="priority_medium")],
        [InlineKeyboardButton("🟠 High", callback_data="priority_high")],
        [InlineKeyboardButton("🔴 Urgent", callback_data="priority_urgent")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Thank you for the description. Please select the priority level for your ticket:",
        reply_markup=reply_markup
    )

    return SUPPORT_PRIORITY


async def support_priority_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle support ticket priority selection.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: The next conversation state
    """
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    priority = query.data.replace("priority_", "")

    # Save support ticket
    ticket_id = await SupportTicket.create_ticket(
        user_id=user_id,
        subject=context.user_data["support_subject"],
        description=context.user_data["support_description"],
        priority=priority
    )

    if ticket_id:
        await query.edit_message_text(
            f"Thank you for submitting your support ticket (ID: {ticket_id})!\n\n"
            f"Our team will review your ticket and respond as soon as possible. "
            f"You can check the status of your ticket with /ticketstatus {ticket_id}."
        )
    else:
        await query.edit_message_text(
            "There was an error creating your support ticket. Please try again later."
        )

    # Clear conversation state
    context.user_data["creating_ticket"] = False
    context.user_data.pop("support_subject", None)
    context.user_data.pop("support_description", None)

    return ConversationHandler.END


async def ticket_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /ticketstatus command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Check if ticket ID is provided
    if not context.args:
        # Show all user tickets
        tickets = await SupportTicket.get_tickets(user_id=user_id)

        if not tickets:
            await update.message.reply_text(
                "You don't have any support tickets. Use /support to create one."
            )
            return

        # Create message with ticket list
        message = "Your support tickets:\n\n"
        for ticket in tickets:
            status_emoji = {
                "open": "🟢",
                "in_progress": "🟡",
                "resolved": "🟢",
                "closed": "⚫"
            }.get(ticket.status, "⚪")

            message += f"{status_emoji} Ticket #{ticket.ticket_id}: {ticket.subject}\n"
            message += f"Status: {ticket.status.upper()}\n"
            message += f"Created: {ticket.created_at[:10]}\n\n"

        message += "Use /ticketstatus <ticket_id> to view details of a specific ticket."

        await update.message.reply_text(message)
        return

    # Get specific ticket
    try:
        ticket_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "Invalid ticket ID. Please provide a valid ticket ID number."
        )
        return

    ticket = await SupportTicket.get_ticket(ticket_id)

    if not ticket:
        await update.message.reply_text(
            f"Ticket #{ticket_id} not found. Please check the ticket ID and try again."
        )
        return

    # Check if user owns the ticket
    if ticket.user_id != user_id:
        await update.message.reply_text(
            "You don't have permission to view this ticket."
        )
        return

    # Get ticket responses
    responses = await SupportTicket.get_responses(ticket_id)

    # Create message with ticket details
    status_emoji = {
        "open": "🟢",
        "in_progress": "🟡",
        "resolved": "🟢",
        "closed": "⚫"
    }.get(ticket.status, "⚪")

    priority_emoji = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "urgent": "🔴"
    }.get(ticket.priority, "⚪")

    message = f"{status_emoji} Ticket #{ticket.ticket_id}: {ticket.subject}\n\n"
    message += f"Status: {ticket.status.upper()}\n"
    message += f"Priority: {priority_emoji} {ticket.priority.upper()}\n"
    message += f"Created: {ticket.created_at[:10]}\n\n"
    message += f"Description:\n{ticket.description}\n\n"

    if responses:
        message += "Responses:\n\n"
        for response in responses:
            sender = "Support Team" if response["is_staff"] else "You"
            message += f"{sender} ({response['created_at'][:10]}):\n"
            message += f"{response['content']}\n\n"

    # Create keyboard for adding response
    keyboard = [
        [InlineKeyboardButton(
            "📝 Add Response", callback_data=f"respond_{ticket_id}")],
        [InlineKeyboardButton("✅ Mark as Resolved",
                              callback_data=f"resolve_{ticket_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)


async def cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle cancellation of community-related conversations.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object

    Returns:
        int: ConversationHandler.END
    """
    query = update.callback_query
    await query.answer()

    # Determine what's being cancelled
    if "feedback" in query.data:
        context.user_data["providing_feedback"] = False
        context.user_data.pop("feedback_type", None)
        context.user_data.pop("feedback_content", None)
        message = "Feedback submission cancelled."
    elif "feature" in query.data:
        context.user_data["requesting_feature"] = False
        context.user_data.pop("feature_title", None)
        message = "Feature request cancelled."
    elif "support" in query.data:
        context.user_data["creating_ticket"] = False
        context.user_data.pop("support_subject", None)
        context.user_data.pop("support_description", None)
        message = "Support ticket creation cancelled."
    else:
        message = "Operation cancelled."

    await query.edit_message_text(message)

    return ConversationHandler.END


async def community_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /communitystats command.

    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id

    # Check if user is an admin
    db_user = await User.get_user(user_id)
    if not db_user or not db_user.is_admin:
        await update.message.reply_text(
            "You don't have permission to view community statistics."
        )
        return

    # Get statistics
    feedback_stats = await Feedback.get_feedback_stats()
    feature_stats = await FeatureRequest.get_feature_request_stats()
    support_stats = await SupportTicket.get_support_stats()

    # Create message with statistics
    message = "📊 Community Engagement Statistics 📊\n\n"

    # Feedback stats
    message += "📝 Feedback:\n"
    message += f"Total feedback: {feedback_stats['total']}\n"
    message += "By type:\n"
    for feedback_type, count in feedback_stats['by_type'].items():
        message += f"- {feedback_type}: {count}\n"
    message += f"Average rating: {feedback_stats['average_rating']}/5\n"
    message += f"Recent (30 days): {feedback_stats['recent_count']}\n\n"

    # Feature request stats
    message += "💡 Feature Requests:\n"
    message += f"Total requests: {feature_stats['total']}\n"
    message += "By status:\n"
    for status, count in feature_stats['by_status'].items():
        message += f"- {status}: {count}\n"

    if feature_stats['top_voted']:
        message += "Top voted features:\n"
        for feature in feature_stats['top_voted']:
            message += f"- {feature['title']} ({feature['votes']} votes)\n"
    message += "\n"

    # Support stats
    message += "🛟 Support:\n"
    message += f"Total tickets: {support_stats['total']}\n"
    message += f"Open tickets: {support_stats['open_tickets']}\n"
    message += "By status:\n"
    for status, count in support_stats['by_status'].items():
        message += f"- {status}: {count}\n"
    message += "By priority:\n"
    for priority, count in support_stats['by_priority'].items():
        message += f"- {priority}: {count}\n"
    message += f"Avg. resolution time: {support_stats['avg_resolution_time']} hours\n"

    await update.message.reply_text(message)


# Register the handlers
def register_community_handlers(application):
    """
    Register community-related handlers.

    Args:
        application: The application instance
    """
    from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler

    # Feedback conversation handler
    feedback_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("feedback", feedback_command)],
        states={
            FEEDBACK_TYPE: [
                CallbackQueryHandler(feedback_type_callback,
                                     pattern=r"^feedback_"),
                CallbackQueryHandler(cancel_callback, pattern=r"^cancel_")
            ],
            FEEDBACK_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, feedback_content)],
            FEEDBACK_RATING: [
                CallbackQueryHandler(
                    feedback_rating_callback, pattern=r"^rating_"),
                CallbackQueryHandler(cancel_callback, pattern=r"^cancel_")
            ]
        },
        fallbacks=[CommandHandler(
            "cancel", lambda u, c: ConversationHandler.END)],
        name="feedback_conversation",
        per_message=False
    )
    application.add_handler(feedback_conv_handler)

    # Feature request conversation handler
    feature_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("feature", feature_command)],
        states={
            FEATURE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, feature_title)],
            FEATURE_DESCRIPTION: [MessageHandler(
                filters.TEXT & ~filters.COMMAND, feature_description)]
        },
        fallbacks=[CommandHandler(
            "cancel", lambda u, c: ConversationHandler.END)],
        name="feature_conversation",
        per_message=False
    )
    application.add_handler(feature_conv_handler)

    # Support ticket conversation handler
    support_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("support", support_command)],
        states={
            SUPPORT_SUBJECT: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_subject)],
            SUPPORT_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, support_description)],
            SUPPORT_PRIORITY: [
                CallbackQueryHandler(
                    support_priority_callback, pattern=r"^priority_"),
                CallbackQueryHandler(cancel_callback, pattern=r"^cancel_")
            ]
        },
        fallbacks=[CommandHandler(
            "cancel", lambda u, c: ConversationHandler.END)],
        name="support_conversation",
        per_message=False
    )
    application.add_handler(support_conv_handler)

    # Other handlers
    application.add_handler(CommandHandler(
        "ticketstatus", ticket_status_command))
    application.add_handler(CommandHandler(
        "communitystats", community_stats_command))

    # Add callback query handlers for ticket actions
    # These would need to be implemented separately
