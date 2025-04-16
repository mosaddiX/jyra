# 🏗️ Jyra Architecture Documentation

## System Overview

Jyra is an emotionally intelligent AI companion designed to engage users in conversations while adopting various personas. The system consists of several interconnected components that work together to provide a seamless and personalized user experience.

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  Messaging      │────▶│  Jyra Core      │────▶│  AI Model       │
│  Platform       │     │  Application    │     │  Integration    │
│  (Telegram)     │◀────│                 │◀────│                 │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 │
                        ┌────────▼────────┐
                        │                 │
                        │  Database       │
                        │  (SQLite)       │
                        │                 │
                        └─────────────────┘
```

## Core Components

### 1. Bot Framework
- **Platform Integration**: Uses python-telegram-bot library to interact with Telegram API
- **Command Handler**: Processes user commands and routes them to appropriate handlers
- **Message Processor**: Handles incoming messages and prepares them for AI processing

### 2. Role Management System
- **Role Templates**: Predefined personas with specific traits and behaviors
- **Custom Roles**: User-defined personas with customizable parameters
- **Role Switching**: Mechanism to change between different personas during conversations

### 3. AI Integration
- **Model Client**: Interface with Gemini API (or alternative AI models)
- **Prompt Engineering**: System to craft effective prompts based on roles and context
- **Response Generation**: Processing AI responses and formatting them for users

### 4. Database System
- **User Profiles**: Stores user preferences and selected roles
- **Conversation History**: Maintains context for ongoing conversations
- **Custom Personas**: Saves user-created role definitions

### 5. Memory and Context Management
- **Short-term Memory**: Recent conversation history for immediate context
- **Long-term Memory**: Important user information stored for future reference
- **Context Window**: Management of conversation length for AI processing

## Data Flow

1. **User Input**: User sends message or command to Jyra via Telegram
2. **Command Processing**: If message is a command, it's routed to the appropriate handler
3. **Context Building**: System retrieves conversation history and user preferences
4. **Prompt Creation**: A prompt is crafted based on the selected role and context
5. **AI Processing**: The prompt is sent to the AI model for response generation
6. **Response Delivery**: AI response is formatted and sent back to the user
7. **Memory Update**: Conversation is stored in the database for future context

## Directory Structure

```
jyra/
├── bot/
│   ├── __init__.py
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── command_handlers.py
│   │   ├── command_handlers_sentiment.py
│   │   ├── message_handlers_sentiment.py
│   │   ├── multimodal_handlers.py
│   │   ├── callback_handlers.py
│   │   └── error_handlers.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── context_middleware.py
│   └── utils/
│       ├── __init__.py
│       └── telegram_helpers.py
├── ai/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── gemini_direct.py
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── prompt_templates.py
│   ├── sentiment/
│   │   ├── __init__.py
│   │   └── sentiment_analyzer.py
│   ├── multimodal/
│   │   ├── __init__.py
│   │   ├── image_processor.py
│   │   ├── speech_processor.py
│   │   └── tts_processor.py
│   ├── cache/
│   │   ├── __init__.py
│   │   └── response_cache.py
│   └── utils/
│       ├── __init__.py
│       └── response_formatter.py
├── db/
│   ├── __init__.py
│   ├── init_db.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── memory.py
│   │   └── role.py
│   └── utils/
│       ├── __init__.py
│       └── db_helpers.py
├── roles/
│   ├── __init__.py
│   ├── templates/
│   │   ├── __init__.py
│   │   └── default_roles.py
│   └── utils/
│       ├── __init__.py
│       └── role_helpers.py
├── utils/
│   ├── __init__.py
│   ├── config.py
│   ├── logger.py
│   └── helpers.py
├── data/
│   └── jyra.db
├── logs/
│   └── jyra.log
├── main.py
├── requirements.txt
└── .env
```

## Security Considerations

1. **API Key Management**: All API keys are stored in environment variables, not in code
2. **User Data Protection**: Personal data is minimized and stored securely
3. **Input Validation**: All user inputs are validated before processing
4. **Rate Limiting**: Implemented to prevent abuse of the system
5. **Error Handling**: Comprehensive error handling to prevent information leakage

## Scalability Considerations

1. **Database Optimization**: Indexes and query optimization for faster access
2. **Caching**: Frequently accessed data is cached to reduce database load
3. **Asynchronous Processing**: Non-blocking operations for improved performance
4. **Modular Design**: Components can be upgraded or replaced independently
5. **Configuration Management**: Easy configuration for different deployment environments
