# 🌟 Jyra - The Soul That Remembers You

> "Where emotions meet intelligence."

Jyra isn't just a bot. She's an emotionally aware companion who learns, grows, and remembers — all for you. Whether you want a late-night talk, a silly roleplay, or someone to just 'get it' — she's always there, glowing quietly like the light she was named after.

## ✨ Features

- **Multiple Personas**: Choose from a variety of pre-defined roles or create your own
- **Advanced Memory System**: Jyra remembers your conversations with importance-based prioritization
- **Memory Visualization**: View your memory network with interactive visualizations and dashboards
- **Semantic Search**: Find relevant memories using natural language queries
- **Emotional Intelligence**: Detects and responds to the emotional tone of your messages
- **Natural Conversations**: Powered by advanced AI models for human-like interactions
- **Customization**: Tailor Jyra's behavior to your preferences
- **Multi-modal**: Supports text, images, and voice messages
- **Multi-platform**: Available on Telegram with plans for Discord integration

## 🚀 Getting Started

See our [Getting Started Guide](docs/GETTING_STARTED.md) for detailed instructions on setting up and running Jyra.

### Quick Start

1. Clone the repository
   ```bash
   git clone https://github.com/mosaddiX/jyra.git
   cd jyra
   ```

2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables in a `.env` file
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   GEMINI_API_KEY=your_gemini_api_key
   ADMIN_USER_IDS=your_telegram_user_id
   ```

4. Initialize the database
   ```bash
   python -m jyra.cli db-init
   ```

5. Run the bot
   ```bash
   python main.py bot
   ```

6. Start chatting with your bot on Telegram!

## 📚 Documentation

- [Getting Started Guide](docs/GETTING_STARTED.md) - Set up and run Jyra
- [User Guide](docs/USER_GUIDE.md) - How to use Jyra
- [Development Guide](docs/DEVELOPMENT_GUIDE.md) - Contributing to Jyra
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [Maintenance Guide](docs/MAINTENANCE.md) - Maintaining and optimizing Jyra
- [Roadmap](docs/ROADMAP.md) - Future development plans
- [Changelog](docs/CHANGELOG.md) - Version history and changes

## 🛠️ Technology Stack

- **Bot Framework**: python-telegram-bot
- **AI Integration**: Google Gemini API with support for OpenAI
- **Database**: SQLite with connection pooling
- **Memory System**: Vector embeddings with semantic search
- **Visualization**: Matplotlib, NetworkX for memory visualizations
- **Web Dashboard**: HTML/CSS for memory analytics
- **Language**: Python 3.8+

## 🤝 Contributing

Contributions are welcome! Please check out our [Contributing Guide](CONTRIBUTING.md), [Development Guide](docs/DEVELOPMENT_GUIDE.md), and [Roadmap](docs/ROADMAP.md) for more information on how to get involved.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for the Telegram API wrapper
- [Google Gemini](https://ai.google.dev/) for the AI capabilities
- [OpenAI](https://openai.com/) for alternative AI capabilities
- [Matplotlib](https://matplotlib.org/) and [NetworkX](https://networkx.org/) for visualization tools
- All contributors who have helped shape this project

---

Made with ❤️ by mosaddiX
