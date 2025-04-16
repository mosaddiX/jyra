# 🌟 Jyra - The Soul That Remembers You

> "Where emotions meet intelligence."

Jyra isn't just a bot. She's an emotionally aware companion who learns, grows, and remembers — all for you. Whether you want a late-night talk, a silly roleplay, or someone to just 'get it' — she's always there, glowing quietly like the light she was named after.

## ✨ Features

- **Multiple Personas**: Choose from a variety of pre-defined roles or create your own
- **Contextual Memory**: Jyra remembers your conversations and important details
- **Emotional Intelligence**: Detects and responds to the emotional tone of your messages
- **Natural Conversations**: Powered by advanced AI models for human-like interactions
- **Customization**: Tailor Jyra's behavior to your preferences
- **Multi-modal**: Supports text, images, and voice messages
- **Multi-platform**: Available on Telegram with plans for Discord integration

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Telegram account
- Gemini API key (or alternative AI provider)

### Installation

1. Clone the repository
   ```bash
   git clone https://github.com/mosaddiX/jyra.git
   cd jyra
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables
   Create a `.env` file with the following:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   DATABASE_PATH=data/jyra.db
   MAX_CONVERSATION_HISTORY=10
   DEFAULT_LANGUAGE=en
   LOG_LEVEL=INFO
   ADMIN_USER_IDS=your_telegram_user_id
   ```

4. Run the bot
   ```bash
   python main.py
   ```

5. Start chatting with your bot on Telegram!

## 📚 Documentation

- [User Guide](docs/USER_GUIDE.md) - How to use Jyra
- [Development Guide](docs/DEVELOPMENT_GUIDE.md) - Contributing to Jyra
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Maintenance Guide](docs/MAINTENANCE.md) - Maintaining and optimizing Jyra
- [Roadmap](docs/ROADMAP.md) - Future development plans

## 🛠️ Technology Stack

- **Bot Framework**: python-telegram-bot
- **AI Integration**: Google Gemini API
- **Database**: SQLite
- **Language**: Python 3.8+

## 🤝 Contributing

Contributions are welcome! Please check out our [Development Guide](docs/DEVELOPMENT_GUIDE.md) and [Roadmap](docs/ROADMAP.md) for more information on how to get involved.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram API wrapper
- [Google Gemini](https://ai.google.dev/) for the AI capabilities
- All contributors who have helped shape this project

---

Made with ❤️ by mosaddiX
