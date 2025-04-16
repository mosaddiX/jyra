# 👨‍💻 Jyra Development Guide

This guide provides information for developers who want to contribute to or modify the Jyra AI companion.

## Development Environment Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Git

### Setting Up the Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/mosaddix/jyra.git
   cd jyra
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root with the following variables:
   ```
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token

   # AI API Configuration
   GEMINI_API_KEY=your_gemini_api_key

   # Database Configuration
   DATABASE_PATH=data/jyra.db

   # Bot Configuration
   MAX_CONVERSATION_HISTORY=10
   DEFAULT_LANGUAGE=en
   LOG_LEVEL=INFO

   # Admin Configuration
   ADMIN_USER_IDS=your_telegram_user_id
   ```

5. **Initialize the database**
   ```bash
   python -m jyra.db.init_db
   ```

## Project Structure

The project follows a modular architecture to separate concerns and make the codebase maintainable:

- `bot/` - Telegram bot implementation
- `ai/` - AI model integration
- `db/` - Database models and utilities
- `roles/` - Role templates and management
- `utils/` - Shared utilities
- `data/` - Data storage
- `logs/` - Log files
- `docs/` - Documentation

## Core Components

### Bot Module
The bot module handles all interactions with the Telegram API:

- `handlers/` - Command and message handlers
- `middleware/` - Processing middleware for messages
- `utils/` - Telegram-specific utilities

### AI Module
The AI module manages interactions with AI models:

- `models/` - Implementations for different AI providers
- `prompts/` - Templates for generating effective prompts
- `utils/` - AI-specific utilities

### Database Module
The database module handles data persistence:

- `models/` - ORM models for database tables
- `utils/` - Database helper functions

### Roles Module
The roles module manages the different personas Jyra can adopt:

- `templates/` - Predefined role templates
- `utils/` - Role management utilities

## Development Workflow

### Adding a New Feature

1. **Create a new branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Implement your changes**
   - Follow the existing code style
   - Add appropriate documentation
   - Write tests for your feature

3. **Run tests**
   ```bash
   pytest
   ```

4. **Submit a pull request**
   - Provide a clear description of your changes
   - Reference any related issues

### Adding a New Role Template

1. Open `roles/templates/default_roles.py`
2. Add your new role following the existing pattern:
   ```python
   "role_name": {
       "name": "Display Name",
       "description": "Brief description of the role",
       "personality": "Detailed personality traits",
       "speaking_style": "How this role communicates",
       "knowledge_areas": ["Area 1", "Area 2"],
       "behaviors": ["Behavior 1", "Behavior 2"]
   }
   ```

### Modifying AI Prompts

1. Open `ai/prompts/prompt_templates.py`
2. Modify the existing templates or add new ones
3. Test thoroughly to ensure the AI responds appropriately

## Testing

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_bot.py

# Run with coverage report
pytest --cov=.
```

### Test Structure
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Tests for component interactions
- `tests/e2e/` - End-to-end tests simulating user interactions

## Deployment

### Local Deployment
```bash
python main.py
```

### Production Deployment
For production, we recommend:
1. Using a process manager like Supervisor
2. Setting up monitoring
3. Configuring regular backups of the database

Example Supervisor configuration:
```ini
[program:jyra]
command=/path/to/venv/bin/python /path/to/jyra/main.py
directory=/path/to/jyra
user=username
autostart=true
autorestart=true
stderr_logfile=/path/to/jyra/logs/supervisor.err.log
stdout_logfile=/path/to/jyra/logs/supervisor.out.log
```

## Troubleshooting

### Common Development Issues

**Database schema errors**
- Check if your database schema is up to date
- Run `python update_db_schema.py` to update the database schema

**API rate limiting**
- Use mock responses during development
- Implement caching to reduce API calls

**Telegram API issues**
- Verify your bot token is correct
- Check Telegram's status page for outages

## Contributing Guidelines

1. Follow PEP 8 style guidelines
2. Write docstrings for all functions and classes
3. Include appropriate error handling
4. Add tests for new functionality
5. Update documentation to reflect changes

## Resources

- [python-telegram-bot Documentation](https://python-telegram-bot.readthedocs.io/)
- [Google Gemini API Documentation](https://ai.google.dev/docs)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Python asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
