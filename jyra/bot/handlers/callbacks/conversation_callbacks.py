"""
Callback handlers for conversation controls.
"""

from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from jyra.db.models.user import User
from jyra.db.models.conversation import Conversation
from jyra.db.models.memory import Memory
from jyra.ui.buttons import create_callback_button, create_main_menu_keyboard
from jyra.ui.formatting import bold, italic, emoji_prefix
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

async def handle_conversation_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle conversation-related callback queries.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    user_id = update.effective_user.id
    
    if callback_data == "conversation_regenerate":
        # Regenerate the last response
        await handle_regenerate(update, context)
    
    elif callback_data == "conversation_save":
        # Save the conversation
        await handle_save_conversation(update, context)
    
    elif callback_data == "conversation_explain":
        # Explain the response
        await handle_explain_response(update, context)
    
    elif callback_data == "conversation_switch_role":
        # Switch role
        from jyra.bot.handlers.callbacks.role_callbacks import handle_roles_menu
        await handle_roles_menu(update, context)
    
    elif callback_data == "conversation_remember":
        # Remember something from the conversation
        await handle_remember_from_conversation(update, context)
    
    elif callback_data == "conversation_end_topic":
        # End the current topic
        await handle_end_topic(update, context)
    
    elif callback_data.startswith("conversation_history_"):
        # View conversation history
        page = int(callback_data.split("_")[-1])
        await handle_view_history(update, context, page)
    
    else:
        logger.warning(f"Unknown conversation callback: {callback_data}")
        await query.message.reply_text(
            "Sorry, I don't recognize that conversation action."
        )

async def handle_regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Regenerate the last response.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get the last conversation message
    last_message = await Conversation.get_last_message(user_id)
    
    if not last_message:
        await query.message.reply_text(
            "I couldn't find our last conversation to regenerate a response."
        )
        return
    
    # Show processing message
    processing_message = await query.message.reply_text(
        "I'm regenerating my response..."
    )
    
    try:
        # Get user's current role
        user = await User.get_user(user_id)
        role_id = user.current_role_id if user else None
        
        # Get the AI model
        from jyra.ai.models.gemini_direct import GeminiAI
        gemini_ai = GeminiAI()
        
        # Get conversation history
        conversation_history = await Conversation.get_conversation_history(user_id, role_id, limit=5)
        
        # Get role context
        from jyra.db.models.role import Role
        role = await Role.get_role(role_id) if role_id else None
        
        role_context = {
            "name": role.name if role else "AI Assistant",
            "personality": role.personality if role else "Helpful and friendly",
            "speaking_style": role.speaking_style if role else "Conversational",
            "knowledge_areas": role.knowledge_areas if role else "General knowledge",
            "behaviors": role.behaviors if role else "Responds helpfully"
        }
        
        # Generate new response
        new_response = await gemini_ai.generate_response(
            prompt=last_message.user_message,
            role_context=role_context,
            conversation_history=conversation_history[:-1]  # Exclude the last message
        )
        
        # Update the conversation in the database
        await Conversation.update_bot_response(last_message.conversation_id, new_response)
        
        # Create conversation controls
        from jyra.ui.keyboards import create_conversation_controls
        keyboard = create_conversation_controls()
        
        # Delete the processing message
        await processing_message.delete()
        
        # Send the new response
        await query.message.reply_text(
            new_response,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error regenerating response: {str(e)}")
        await processing_message.edit_text(
            "Sorry, I had trouble regenerating my response. Please try again later."
        )

async def handle_save_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Save the current conversation.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get the conversation history
    user = await User.get_user(user_id)
    role_id = user.current_role_id if user else None
    
    conversation_history = await Conversation.get_conversation_history(user_id, role_id, limit=10)
    
    if not conversation_history:
        await query.message.reply_text(
            "There's no conversation to save yet."
        )
        return
    
    # Format the conversation
    formatted_conversation = "# Saved Conversation\n\n"
    
    for i, message in enumerate(conversation_history):
        if i % 2 == 0:
            formatted_conversation += f"**You:** {message.user_message}\n\n"
        else:
            formatted_conversation += f"**Jyra:** {message.bot_response}\n\n"
    
    # Create a unique filename
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"conversation_{timestamp}.md"
    
    # Save the conversation
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(formatted_conversation)
        
        await query.message.reply_text(
            f"I've saved our conversation to {filename}."
        )
    except Exception as e:
        logger.error(f"Error saving conversation: {str(e)}")
        await query.message.reply_text(
            "Sorry, I had trouble saving our conversation. Please try again later."
        )

async def handle_explain_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Explain the last response.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get the last conversation message
    last_message = await Conversation.get_last_message(user_id)
    
    if not last_message:
        await query.message.reply_text(
            "I couldn't find our last conversation to explain."
        )
        return
    
    # Show processing message
    processing_message = await query.message.reply_text(
        "I'm preparing an explanation of my response..."
    )
    
    try:
        # Get the AI model
        from jyra.ai.models.gemini_direct import GeminiAI
        gemini_ai = GeminiAI()
        
        # Generate explanation
        explanation_prompt = f"""
        You recently gave the following response to a user:
        
        "{last_message.bot_response}"
        
        Please explain your reasoning and thought process behind this response in a clear, 
        concise way. Break down why you responded this way and what factors influenced your answer.
        """
        
        explanation = await gemini_ai.generate_response(
            prompt=explanation_prompt,
            role_context={"name": "Explainer", "personality": "Clear and educational"},
            conversation_history=[]
        )
        
        # Delete the processing message
        await processing_message.delete()
        
        # Send the explanation
        await query.message.reply_text(
            f"{bold('Explanation of my response:')}\n\n{explanation}"
        )
        
    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        await processing_message.edit_text(
            "Sorry, I had trouble explaining my response. Please try again later."
        )

async def handle_remember_from_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Extract and remember information from the conversation.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get the conversation history
    user = await User.get_user(user_id)
    role_id = user.current_role_id if user else None
    
    conversation_history = await Conversation.get_conversation_history(user_id, role_id, limit=5)
    
    if not conversation_history:
        await query.message.reply_text(
            "There's no conversation to extract memories from yet."
        )
        return
    
    # Show processing message
    processing_message = await query.message.reply_text(
        "I'm analyzing our conversation for important information to remember..."
    )
    
    try:
        # Get the AI model
        from jyra.ai.models.gemini_direct import GeminiAI
        gemini_ai = GeminiAI()
        
        # Format conversation for analysis
        conversation_text = ""
        for message in conversation_history:
            conversation_text += f"User: {message.user_message}\nAI: {message.bot_response}\n\n"
        
        # Generate memory extraction prompt
        memory_prompt = f"""
        Analyze the following conversation and extract 1-3 important pieces of information about the user 
        that should be remembered for future conversations. Focus on personal details, preferences, 
        or important facts. Format each memory as a separate, concise statement.
        
        Conversation:
        {conversation_text}
        
        Extract memories in this format:
        1. [Memory 1]
        2. [Memory 2]
        3. [Memory 3]
        
        If no clear memories can be extracted, respond with "No clear memories to extract."
        """
        
        memory_extraction = await gemini_ai.generate_response(
            prompt=memory_prompt,
            role_context={"name": "Memory Extractor", "personality": "Analytical and precise"},
            conversation_history=[]
        )
        
        # Parse extracted memories
        memories = []
        for line in memory_extraction.split("\n"):
            if line.strip() and line[0].isdigit() and ". " in line:
                memory_text = line.split(". ", 1)[1].strip()
                if memory_text and memory_text != "[Memory 1]" and not memory_text.startswith("["):
                    memories.append(memory_text)
        
        # Delete the processing message
        await processing_message.delete()
        
        if not memories or "No clear memories" in memory_extraction:
            await query.message.reply_text(
                "I couldn't find any clear information to remember from our recent conversation."
            )
            return
        
        # Create buttons for each memory
        keyboard = []
        for i, memory in enumerate(memories):
            keyboard.append([
                create_callback_button(f"Remember: {memory[:30]}...", f"save_memory_{i}")
            ])
        
        # Add cancel button
        keyboard.append([
            create_callback_button("Cancel", "cancel_memory")
        ])
        
        # Store memories in context for later use
        context.user_data["extracted_memories"] = memories
        
        # Send memory selection message
        await query.message.reply_text(
            f"{bold('I found these potential memories:')}\n\n" + 
            "\n".join([f"{i+1}. {memory}" for i, memory in enumerate(memories)]) +
            "\n\nSelect which ones you'd like me to remember:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Error extracting memories: {str(e)}")
        await processing_message.edit_text(
            "Sorry, I had trouble analyzing our conversation. Please try again later."
        )

async def handle_end_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    End the current conversation topic.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Clear conversation context
    context.user_data["conversation_context"] = {}
    
    # Create main menu keyboard
    keyboard = create_main_menu_keyboard()
    
    await query.message.reply_text(
        f"{bold('Topic Ended')}\n\nI've cleared our current conversation context. What would you like to talk about next?",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def handle_view_history(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0) -> None:
    """
    View conversation history.
    
    Args:
        update (Update): The update object
        context (ContextTypes.DEFAULT_TYPE): The context object
        page (int): The page number to view
    """
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Get the conversation history
    user = await User.get_user(user_id)
    role_id = user.current_role_id if user else None
    
    # Get total conversation count
    total_count = await Conversation.get_conversation_count(user_id, role_id)
    
    if total_count == 0:
        await query.message.reply_text(
            "You don't have any conversation history yet."
        )
        return
    
    # Calculate pagination
    page_size = 5
    total_pages = (total_count + page_size - 1) // page_size
    
    if page < 0:
        page = 0
    elif page >= total_pages:
        page = total_pages - 1
    
    # Get paginated conversation history
    conversation_history = await Conversation.get_conversation_history(
        user_id, role_id, limit=page_size, offset=page * page_size
    )
    
    if not conversation_history:
        await query.message.reply_text(
            "I couldn't retrieve your conversation history."
        )
        return
    
    # Format the conversation history
    history_text = f"{bold('Conversation History')} (Page {page + 1}/{total_pages})\n\n"
    
    for i, message in enumerate(conversation_history):
        # Add timestamp
        timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M:%S") if message.timestamp else "Unknown time"
        
        if i % 2 == 0:
            # User message
            history_text += f"{bold('You')} ({timestamp}):\n{message.user_message}\n\n"
        else:
            # Bot response
            history_text += f"{bold('Jyra')}:\n{message.bot_response[:100]}...\n\n"
    
    # Create navigation buttons
    keyboard = []
    nav_row = []
    
    if page > 0:
        nav_row.append(create_callback_button("⬅️ Previous", f"conversation_history_{page - 1}"))
    
    if page < total_pages - 1:
        nav_row.append(create_callback_button("➡️ Next", f"conversation_history_{page + 1}"))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Add back button
    keyboard.append([create_callback_button("⬅️ Back to Menu", "menu_main")])
    
    await query.message.edit_text(
        history_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='HTML'
    )
