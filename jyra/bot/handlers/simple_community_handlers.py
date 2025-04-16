"""
Simplified community engagement handlers for Jyra Telegram bot.
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from jyra.community.feedback import Feedback
from jyra.community.feature_requests import FeatureRequest
from jyra.community.support import SupportTicket
from jyra.db.models.user import User
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)


async def feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /feedback command.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "Thank you for wanting to provide feedback! To submit feedback, please use one of these commands:\n\n"
        "/bugreport - Report a bug or issue\n"
        "/featurerequest - Suggest a new feature\n"
        "/generalfeedback - Share your general thoughts about Jyra"
    )


async def bug_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /bugreport command.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "Please describe the bug you've encountered in detail. Include what you were doing, "
        "what you expected to happen, and what actually happened instead."
    )
    
    # Set the next handler
    context.user_data["expecting_bug_report"] = True


async def feature_request_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /featurerequest command.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "Please describe the feature you'd like to see in Jyra. Include what problem it would solve "
        "and how you envision it working."
    )
    
    # Set the next handler
    context.user_data["expecting_feature_request"] = True


async def general_feedback_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /generalfeedback command.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "Please share your thoughts, experiences, or suggestions about Jyra. "
        "What do you like? What could be improved?"
    )
    
    # Set the next handler
    context.user_data["expecting_general_feedback"] = True


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /support command.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "Need help with Jyra? Please describe your issue in detail, and we'll get back to you as soon as possible."
    )
    
    # Set the next handler
    context.user_data["expecting_support_request"] = True


async def ticket_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /ticketstatus command.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    
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
    
    await update.message.reply_text(message)


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


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle messages for community engagement.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # Check if we're expecting a specific type of input
    if context.user_data.get("expecting_bug_report"):
        # Handle bug report
        await Feedback.add_feedback(
            user_id=user_id,
            feedback_type="bug",
            content=message_text,
            rating=0
        )
        
        await update.message.reply_text(
            "Thank you for reporting this bug! Your report has been recorded and will be reviewed by our team."
        )
        
        # Clear the flag
        context.user_data["expecting_bug_report"] = False
        return True
    
    elif context.user_data.get("expecting_feature_request"):
        # Handle feature request
        request_id = await FeatureRequest.add_feature_request(
            user_id=user_id,
            title=message_text[:50] + ("..." if len(message_text) > 50 else ""),
            description=message_text
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
        
        # Clear the flag
        context.user_data["expecting_feature_request"] = False
        return True
    
    elif context.user_data.get("expecting_general_feedback"):
        # Handle general feedback
        await Feedback.add_feedback(
            user_id=user_id,
            feedback_type="general",
            content=message_text,
            rating=5  # Default to 5 stars
        )
        
        await update.message.reply_text(
            "Thank you for your feedback! It has been recorded and will help us improve Jyra."
        )
        
        # Clear the flag
        context.user_data["expecting_general_feedback"] = False
        return True
    
    elif context.user_data.get("expecting_support_request"):
        # Handle support request
        ticket_id = await SupportTicket.create_ticket(
            user_id=user_id,
            subject=message_text[:50] + ("..." if len(message_text) > 50 else ""),
            description=message_text,
            priority="medium"  # Default to medium priority
        )
        
        if ticket_id:
            await update.message.reply_text(
                f"Thank you for submitting your support ticket (ID: {ticket_id})!\n\n"
                f"Our team will review your ticket and respond as soon as possible. "
                f"You can check the status of your ticket with /ticketstatus."
            )
        else:
            await update.message.reply_text(
                "There was an error creating your support ticket. Please try again later."
            )
        
        # Clear the flag
        context.user_data["expecting_support_request"] = False
        return True
    
    # If we're not expecting any specific input, return False to let other handlers process the message
    return False


# Register the handlers
def register_community_handlers(application):
    """
    Register community-related handlers.
    
    Args:
        application: The application instance
    """
    # Register command handlers
    application.add_handler(CommandHandler("feedback", feedback_command))
    application.add_handler(CommandHandler("bugreport", bug_report_command))
    application.add_handler(CommandHandler("featurerequest", feature_request_command))
    application.add_handler(CommandHandler("generalfeedback", general_feedback_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("ticketstatus", ticket_status_command))
    application.add_handler(CommandHandler("communitystats", community_stats_command))
