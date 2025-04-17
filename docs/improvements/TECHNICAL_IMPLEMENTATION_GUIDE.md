# Jyra Bot Technical Implementation Guide

This document provides technical guidance for implementing the improvements outlined in the companion documents. It focuses on code structure, best practices, and specific implementation details.

## Code Structure Improvements

### 1. Modularize Command Handlers

**Current Structure:**
- Large handler files with multiple command functions
- Limited separation of concerns

**Improved Structure:**
```
jyra/
├── bot/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── base_handler.py  # New abstract base class
│   │   ├── commands/  # New directory for command modules
│   │   │   ├── __init__.py
│   │   │   ├── start_command.py
│   │   │   ├── help_command.py
│   │   │   ├── role_command.py
│   │   │   └── ...
│   │   ├── callbacks/  # New directory for callback handlers
│   │   │   ├── __init__.py
│   │   │   ├── menu_callbacks.py
│   │   │   ├── role_callbacks.py
│   │   │   └── ...
│   │   └── ...
```

**Implementation Steps:**
1. Create a base handler class with common functionality
2. Split command handlers into individual modules
3. Implement registration system for handlers
4. Create utility functions for common operations

---

### 2. UI Component System

**Current Structure:**
- Inline button creation scattered throughout code
- Inconsistent message formatting

**Improved Structure:**
```
jyra/
├── ui/  # New module for UI components
│   ├── __init__.py
│   ├── buttons.py  # Button factories and layouts
│   ├── messages.py  # Message templates
│   ├── keyboards.py  # Keyboard layouts
│   ├── formatting.py  # Text formatting utilities
│   └── components/  # Reusable UI components
│       ├── __init__.py
│       ├── pagination.py
│       ├── selection_list.py
│       └── ...
```

**Implementation Steps:**
1. Create button factory functions for consistent styling
2. Implement message template system
3. Create keyboard layout generators
4. Build reusable UI components for common patterns

---

### 3. State Management

**Current Structure:**
- Limited conversation state tracking
- Context data scattered across handlers

**Improved Structure:**
```
jyra/
├── state/  # New module for state management
│   ├── __init__.py
│   ├── conversation_state.py
│   ├── user_state.py
│   ├── session_state.py
│   └── state_manager.py
```

**Implementation Steps:**
1. Create centralized state management system
2. Implement conversation state tracking
3. Add user session management
4. Create state persistence layer

## Technical Implementation Details

### 1. Command Handler Improvements

#### Base Handler Class

```python
# jyra/bot/handlers/base_handler.py
from abc import ABC, abstractmethod
from telegram import Update
from telegram.ext import ContextTypes

class BaseHandler(ABC):
    """Base class for all command handlers."""
    
    @abstractmethod
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the command."""
        pass
        
    async def pre_handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Pre-processing before handling the command. Return False to abort."""
        # Common pre-processing like user validation, rate limiting, etc.
        return True
        
    async def post_handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Post-processing after handling the command."""
        # Common post-processing like logging, analytics, etc.
        pass
        
    @classmethod
    async def execute(cls, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Execute the handler with pre and post processing."""
        handler = cls()
        if await handler.pre_handle(update, context):
            await handler.handle(update, context)
            await handler.post_handle(update, context)
```

#### Example Command Implementation

```python
# jyra/bot/handlers/commands/start_command.py
from jyra.bot.handlers.base_handler import BaseHandler
from jyra.ui.buttons import create_main_menu_buttons
from jyra.ui.messages import welcome_message_template
from jyra.db.models.user import User

class StartCommandHandler(BaseHandler):
    """Handler for the /start command."""
    
    async def handle(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle the /start command."""
        user = update.effective_user
        
        # Get or create user in database
        db_user = await User.get_user(user.id)
        if not db_user:
            db_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code
            )
            await db_user.save()
            
            # New user welcome
            welcome_text = welcome_message_template.format(
                name=user.first_name or "there",
                is_new_user=True
            )
            
            # Set onboarding state
            context.user_data["onboarding_state"] = "welcome"
        else:
            # Returning user welcome
            welcome_text = welcome_message_template.format(
                name=user.first_name or "there",
                is_new_user=False
            )
        
        # Create main menu buttons
        keyboard = create_main_menu_buttons()
        
        # Send welcome message with menu
        await update.message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # If new user, start onboarding sequence
        if not db_user.created_at:
            context.job_queue.run_once(
                self.send_onboarding_step,
                3,  # 3 second delay
                data={
                    "user_id": user.id,
                    "chat_id": update.effective_chat.id,
                    "step": 1
                }
            )
    
    async def send_onboarding_step(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Send an onboarding step message."""
        job_data = context.job.data
        chat_id = job_data["chat_id"]
        step = job_data["step"]
        
        # Get onboarding content for this step
        from jyra.ui.onboarding import get_onboarding_step
        content, keyboard = get_onboarding_step(step)
        
        # Send the onboarding message
        await context.bot.send_message(
            chat_id=chat_id,
            text=content,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
```

---

### 2. UI Component System

#### Button Factory

```python
# jyra/ui/buttons.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict, Any, Optional, Union

def create_button(text: str, callback_data: str = None, url: str = None) -> InlineKeyboardButton:
    """Create a styled button with consistent formatting."""
    if url:
        return InlineKeyboardButton(text, url=url)
    return InlineKeyboardButton(text, callback_data=callback_data)

def create_main_menu_buttons() -> InlineKeyboardMarkup:
    """Create the main menu button layout."""
    keyboard = [
        [
            create_button("🎭 Roles", callback_data="menu_roles"),
            create_button("🧠 Memory", callback_data="menu_memory")
        ],
        [
            create_button("⚙️ Settings", callback_data="menu_settings"),
            create_button("❓ Help", callback_data="menu_help")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_role_selection_buttons(roles: List[Dict[str, Any]], 
                                 page: int = 0, 
                                 page_size: int = 6) -> InlineKeyboardMarkup:
    """Create paginated role selection buttons."""
    # Calculate pagination
    total_pages = (len(roles) + page_size - 1) // page_size
    start_idx = page * page_size
    end_idx = min(start_idx + page_size, len(roles))
    
    # Create role buttons (2 per row)
    keyboard = []
    current_row = []
    
    for i in range(start_idx, end_idx):
        role = roles[i]
        button = create_button(
            f"{role.get('emoji', '')} {role['name']}", 
            callback_data=f"role_{role['role_id']}"
        )
        
        current_row.append(button)
        if len(current_row) == 2:
            keyboard.append(current_row)
            current_row = []
    
    # Add any remaining buttons
    if current_row:
        keyboard.append(current_row)
    
    # Add navigation row
    nav_row = []
    if page > 0:
        nav_row.append(create_button("⬅️ Previous", callback_data=f"roles_page_{page-1}"))
    
    nav_row.append(create_button("📋 Categories", callback_data="roles_categories"))
    
    if page < total_pages - 1:
        nav_row.append(create_button("➡️ Next", callback_data=f"roles_page_{page+1}"))
    
    keyboard.append(nav_row)
    
    # Add back button
    keyboard.append([create_button("⬅️ Back to Menu", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(keyboard)
```

#### Message Templates

```python
# jyra/ui/messages.py
from typing import Dict, Any

# Welcome message template
welcome_message_template = """
<b>Welcome to Jyra{is_new_user and ", " + name or ""}!</b> 🌟

{is_new_user and """
I'm your emotionally intelligent AI companion, designed to remember you and adapt to your needs.

Let's get started on our journey together!
""" or f"""
Welcome back{name and ", " + name or ""}! It's great to see you again.

How can I assist you today?
"""}

Use the buttons below to navigate or type a message to start chatting.
"""

# Help message template
help_message_template = """
<b>Jyra Help Center</b> ❓

{category_content}

Use the buttons below to explore different help categories.
"""

# Role description template
role_description_template = """
<b>{role_name}</b> {role_emoji}

{role_description}

<b>Personality:</b> {personality}
<b>Speaking Style:</b> {speaking_style}
<b>Knowledge Areas:</b> {knowledge_areas}

{is_custom and f"Created by: {created_by}" or ""}

Use the buttons below to select this role or explore others.
"""

def format_message(template: str, **kwargs) -> str:
    """Format a message template with the given parameters."""
    return template.format(**kwargs)
```

---

### 3. State Management

#### Conversation State Manager

```python
# jyra/state/conversation_state.py
from typing import Dict, Any, Optional
from enum import Enum, auto

class ConversationState(Enum):
    """Enum for conversation states."""
    IDLE = auto()
    CHATTING = auto()
    CREATING_ROLE = auto()
    SELECTING_ROLE = auto()
    ADDING_MEMORY = auto()
    CHANGING_SETTINGS = auto()
    ONBOARDING = auto()

class ConversationStateManager:
    """Manager for conversation state."""
    
    def __init__(self):
        self.states: Dict[int, Dict[str, Any]] = {}
    
    def get_state(self, user_id: int) -> Dict[str, Any]:
        """Get the current state for a user."""
        if user_id not in self.states:
            self.states[user_id] = {
                "state": ConversationState.IDLE,
                "data": {},
                "history": []
            }
        return self.states[user_id]
    
    def set_state(self, user_id: int, state: ConversationState, data: Optional[Dict[str, Any]] = None) -> None:
        """Set the state for a user."""
        current = self.get_state(user_id)
        
        # Add current state to history
        current["history"].append({
            "state": current["state"],
            "data": current["data"]
        })
        
        # Limit history length
        if len(current["history"]) > 10:
            current["history"] = current["history"][-10:]
        
        # Set new state
        current["state"] = state
        current["data"] = data or {}
    
    def get_previous_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get the previous state for a user."""
        current = self.get_state(user_id)
        if not current["history"]:
            return None
        return current["history"][-1]
    
    def revert_to_previous_state(self, user_id: int) -> bool:
        """Revert to the previous state for a user."""
        previous = self.get_previous_state(user_id)
        if not previous:
            return False
        
        current = self.get_state(user_id)
        current["state"] = previous["state"]
        current["data"] = previous["data"]
        current["history"] = current["history"][:-1]
        return True

# Create a global instance
conversation_state_manager = ConversationStateManager()
```

## Implementation Strategy

### 1. Refactoring Approach

To minimize disruption while implementing improvements:

1. **Parallel Implementation**: Create new modules alongside existing ones
2. **Incremental Migration**: Gradually move functionality to new structure
3. **Feature Flagging**: Use feature flags to enable/disable new components
4. **Backward Compatibility**: Ensure new components work with existing data

Example feature flag implementation:

```python
# jyra/utils/feature_flags.py
from typing import Dict, Any

# Feature flag definitions
FEATURE_FLAGS = {
    "USE_NEW_UI_COMPONENTS": True,
    "USE_NEW_STATE_MANAGEMENT": False,
    "ENABLE_ADVANCED_ROLES": False,
    "ENABLE_MEMORY_VISUALIZATION": False
}

def is_feature_enabled(feature_name: str) -> bool:
    """Check if a feature is enabled."""
    return FEATURE_FLAGS.get(feature_name, False)
```

### 2. Database Migration Strategy

For database schema changes:

1. Create migration scripts for each schema change
2. Implement version tracking in the database
3. Run migrations automatically on startup
4. Include rollback functionality

Example migration system:

```python
# jyra/db/migrations/migration_manager.py
import sqlite3
from typing import List, Dict, Any
from jyra.utils.config import DATABASE_PATH
from jyra.utils.logger import setup_logger

logger = setup_logger(__name__)

class MigrationManager:
    """Manager for database migrations."""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        
    def get_current_version(self) -> int:
        """Get the current database version."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT version FROM db_version")
            version = cursor.fetchone()[0]
        except sqlite3.OperationalError:
            # Table doesn't exist, create it
            cursor.execute("CREATE TABLE db_version (version INTEGER)")
            cursor.execute("INSERT INTO db_version VALUES (0)")
            conn.commit()
            version = 0
            
        conn.close()
        return version
        
    def set_version(self, version: int) -> None:
        """Set the database version."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE db_version SET version = ?", (version,))
        conn.commit()
        conn.close()
        
    def run_migrations(self, target_version: int = None) -> None:
        """Run all pending migrations."""
        from jyra.db.migrations import migrations
        
        current_version = self.get_current_version()
        if target_version is None:
            target_version = len(migrations)
            
        logger.info(f"Current database version: {current_version}")
        logger.info(f"Target database version: {target_version}")
        
        if current_version == target_version:
            logger.info("Database is up to date")
            return
            
        if current_version > target_version:
            logger.error(f"Cannot downgrade database from {current_version} to {target_version}")
            return
            
        # Run migrations
        for version in range(current_version + 1, target_version + 1):
            if version >= len(migrations):
                break
                
            migration = migrations[version]
            logger.info(f"Running migration {version}: {migration['description']}")
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            try:
                # Run the migration
                migration["up"](cursor)
                conn.commit()
                
                # Update version
                self.set_version(version)
                logger.info(f"Migration {version} completed successfully")
            except Exception as e:
                conn.rollback()
                logger.error(f"Migration {version} failed: {str(e)}")
                raise
            finally:
                conn.close()
```

### 3. Testing Strategy

For testing the new implementations:

1. Create unit tests for all new components
2. Implement integration tests for component interactions
3. Add end-to-end tests for critical user flows
4. Set up CI/CD pipeline for automated testing

Example test for a UI component:

```python
# tests/unit/ui/test_buttons.py
import unittest
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from jyra.ui.buttons import create_button, create_main_menu_buttons

class TestButtons(unittest.TestCase):
    """Tests for button factory functions."""
    
    def test_create_button(self):
        """Test creating a button."""
        # Test callback button
        button = create_button("Test", callback_data="test")
        self.assertIsInstance(button, InlineKeyboardButton)
        self.assertEqual(button.text, "Test")
        self.assertEqual(button.callback_data, "test")
        
        # Test URL button
        button = create_button("Test", url="https://example.com")
        self.assertIsInstance(button, InlineKeyboardButton)
        self.assertEqual(button.text, "Test")
        self.assertEqual(button.url, "https://example.com")
        
    def test_create_main_menu_buttons(self):
        """Test creating main menu buttons."""
        keyboard = create_main_menu_buttons()
        self.assertIsInstance(keyboard, InlineKeyboardMarkup)
        
        # Check structure
        self.assertEqual(len(keyboard.inline_keyboard), 2)
        self.assertEqual(len(keyboard.inline_keyboard[0]), 2)
        self.assertEqual(len(keyboard.inline_keyboard[1]), 2)
        
        # Check button texts
        self.assertEqual(keyboard.inline_keyboard[0][0].text, "🎭 Roles")
        self.assertEqual(keyboard.inline_keyboard[0][1].text, "🧠 Memory")
        self.assertEqual(keyboard.inline_keyboard[1][0].text, "⚙️ Settings")
        self.assertEqual(keyboard.inline_keyboard[1][1].text, "❓ Help")
        
        # Check callback data
        self.assertEqual(keyboard.inline_keyboard[0][0].callback_data, "menu_roles")
        self.assertEqual(keyboard.inline_keyboard[0][1].callback_data, "menu_memory")
        self.assertEqual(keyboard.inline_keyboard[1][0].callback_data, "menu_settings")
        self.assertEqual(keyboard.inline_keyboard[1][1].callback_data, "menu_help")
```

## Implementation Checklist

### Phase 1: Foundation

- [ ] Set up bot profile with BotFather
- [ ] Create UI component system
- [ ] Implement base handler class
- [ ] Set up state management system
- [ ] Create database migration system
- [ ] Implement feature flag system
- [ ] Add unit tests for new components

### Phase 2: Command Improvements

- [ ] Refactor start command
- [ ] Implement help command improvements
- [ ] Enhance role selection interface
- [ ] Improve settings menu
- [ ] Update about command
- [ ] Add integration tests for commands

### Phase 3: Feature Enhancements

- [ ] Implement memory system improvements
- [ ] Enhance conversation handling
- [ ] Add advanced role features
- [ ] Improve sentiment analysis
- [ ] Implement multi-modal enhancements
- [ ] Add end-to-end tests for features

### Phase 4: Polish and Optimization

- [ ] Implement accessibility improvements
- [ ] Add animations and transitions
- [ ] Optimize performance
- [ ] Enhance error handling
- [ ] Implement analytics
- [ ] Conduct user testing
- [ ] Create final documentation

## Best Practices

### 1. Code Style

- Follow PEP 8 style guidelines
- Use consistent naming conventions
- Add type hints to all functions
- Write comprehensive docstrings
- Use meaningful variable names

### 2. Error Handling

- Use try/except blocks for all external operations
- Implement graceful degradation
- Log all errors with context
- Provide user-friendly error messages
- Add error reporting for critical failures

### 3. Performance

- Use asynchronous operations where possible
- Implement caching for expensive operations
- Optimize database queries
- Minimize external API calls
- Use connection pooling for database access

### 4. Security

- Validate all user inputs
- Use parameterized queries for database operations
- Implement rate limiting
- Secure API keys and sensitive data
- Add input sanitization for all user-generated content

## Conclusion

This technical implementation guide provides a structured approach to implementing the improvements outlined in the companion documents. By following these guidelines, developers can ensure a consistent, maintainable, and high-quality implementation of the Jyra bot improvements.
