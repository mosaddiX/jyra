# Getting Started with Jyra

Welcome to Jyra, the emotionally intelligent AI companion! This guide will help you set up and start using Jyra.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.8 or higher
- pip (Python package manager)
- Git (for cloning the repository)
- A Telegram account and bot token (for bot functionality)
- A Google Gemini API key (for AI capabilities)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mosaddiX/jyra.git
cd jyra
```

### 2. Create a Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root directory with the following content:

```
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key

# Database Configuration
DATABASE_PATH=data/jyra.db

# Bot Configuration
MAX_CONVERSATION_HISTORY=10
LOG_LEVEL=INFO

# Admin Configuration
ADMIN_USER_IDS=your_telegram_user_id
```

Replace the placeholder values with your actual credentials:
- `your_telegram_bot_token`: Get this by creating a new bot with [@BotFather](https://t.me/botfather) on Telegram
- `your_gemini_api_key`: Get this from the [Google AI Studio](https://ai.google.dev/)
- `your_telegram_user_id`: Your Telegram user ID (you can get this from [@userinfobot](https://t.me/userinfobot))

### 5. Initialize the Database

```bash
python -m jyra.db.init_db
```

## Running Jyra

To start the bot, run:

```bash
python main.py
```

The bot will now be online and ready to receive messages on Telegram.

## Using Jyra

Once the bot is running, you can interact with it on Telegram. Here are some commands to get started:

- `/start` - Begin your journey with Jyra
- `/help` - Display help message with available commands
- `/role` - Choose a roleplay persona for Jyra
- `/switchrole` - Change to a different roleplay persona
- `/createrole` - Create your own custom persona
- `/remember` - Tell Jyra something important to remember
- `/forget` - Ask Jyra to forget a specific memory
- `/mood` - Check your emotional trends based on conversations
- `/voice` - Toggle voice responses on/off
- `/settings` - Adjust your preferences for Jyra
- `/about` - Learn more about Jyra

## Features

### Roleplay Personas

Jyra comes with several predefined personas, each with unique characteristics:

- **Friend** - A casual, supportive companion for everyday chat
- **Mentor** - A wise guide offering advice and encouragement
- **Therapist** - A compassionate listener providing emotional support
- **Detective** - A sharp-minded investigator who loves solving mysteries
- **Adventurer** - An enthusiastic explorer ready for imaginary journeys
- **Philosopher** - A deep thinker who ponders life's big questions
- **Comedian** - A humorous character who tries to make you laugh
- **Storyteller** - A creative narrator who can spin tales and scenarios

You can also create your own custom personas using the `/createrole` command.

### Memory System

Jyra can remember important details about you and your conversations. Use the `/remember` command to explicitly tell Jyra something you want it to remember.

### Emotional Intelligence

Jyra can detect the emotional tone of your messages and respond appropriately. The `/mood` command shows trends in your emotional states based on your conversations.

### Multi-modal Support

Jyra can process and respond to:
- Text messages
- Voice messages (speech-to-text)
- Images (with descriptions)

## Troubleshooting

### Common Issues

**Bot not responding**
- Check if the bot is running in your terminal
- Verify your Telegram bot token is correct
- Ensure you have an active internet connection

**AI responses not working**
- Verify your Gemini API key is correct
- Check your API usage limits
- Ensure the model is available in your region

**Database errors**
- Run `python -m jyra.db.init_db` to reinitialize the database
- Check if the database path in `.env` is correct

## Maintenance

For regular maintenance tasks, you can use:

```bash
# Optimize the database
python run_maintenance.py optimize_db

# Clear the cache
python run_maintenance.py clear_cache

# Run security checks
python run_maintenance.py security_check
```

## Next Steps

For more detailed information, check out:
- [User Guide](USER_GUIDE.md) - Comprehensive guide for users
- [Development Guide](DEVELOPMENT_GUIDE.md) - Guide for developers
- [Architecture Documentation](ARCHITECTURE.md) - Technical architecture details
- [Roadmap](ROADMAP.md) - Future development plans

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.
