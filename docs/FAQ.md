# Frequently Asked Questions (FAQ)

This document answers common questions about Jyra.

## General Questions

### What is Jyra?

Jyra is an emotionally intelligent AI companion designed to engage users in conversations while adopting various personas. The name "Jyra" is a fusion of Jyoti (light) and Aura (presence, emotion) - a name born from light, designed to listen, respond, and understand.

### What makes Jyra different from other chatbots?

Jyra stands out with its:
- **Emotional intelligence**: Detects and responds to your emotional state
- **Memory system**: Remembers important details about you and your conversations
- **Roleplay capabilities**: Can adopt different personas to suit your preferences
- **Multi-modal support**: Handles text, images, and voice messages

### Is Jyra free to use?

Yes, Jyra is an open-source project that you can use for free. However, you'll need to provide your own API keys for the AI model (Google Gemini).

### What platforms does Jyra support?

Currently, Jyra works with Telegram. We plan to add Discord support in the future.

## Setup and Installation

### What do I need to run Jyra?

To run Jyra, you need:
- Python 3.8 or higher
- A Telegram bot token (from BotFather)
- A Google Gemini API key
- Basic knowledge of command-line interfaces

### How do I get a Telegram bot token?

1. Open Telegram and search for @BotFather
2. Start a chat and send /newbot
3. Follow the instructions to create a new bot
4. BotFather will give you a token - copy this for your .env file

### How do I get a Google Gemini API key?

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Navigate to the API keys section
4. Create a new API key and copy it for your .env file

### I'm getting an error during installation. What should I do?

Check our [Troubleshooting Guide](MAINTENANCE.md#troubleshooting) for common issues and solutions. If your issue isn't covered, please report it on our [GitHub Issues](https://github.com/mosaddiX/jyra/issues) page.

## Usage

### How do I start a conversation with Jyra?

After setting up Jyra, find your bot on Telegram and send the /start command. Jyra will introduce itself and guide you through the initial setup.

### How do I change Jyra's persona?

Use the /role command to see available personas, then select one from the list. You can also create your own custom persona with the /createrole command.

### How does Jyra's memory system work?

Jyra remembers details from your conversations in several ways:
- **Explicit memories**: Things you specifically ask Jyra to remember using the /remember command
- **Extracted memories**: Important information Jyra automatically extracts from your conversations
- **Conversation history**: Recent messages in your current conversation

### Can Jyra understand images?

Yes, Jyra can process images and respond to them. Simply send an image in your chat, and Jyra will analyze it and respond accordingly.

### Can Jyra understand voice messages?

Yes, Jyra can transcribe and respond to voice messages. Send a voice message in your chat, and Jyra will process it and respond to the content.

## Privacy and Security

### Does Jyra store my conversations?

Yes, Jyra stores your conversations in a local database to provide context-aware responses. This data is stored only on the server where you run Jyra, not on any external servers.

### Who can access my data?

Only you and anyone with access to the server where Jyra is running can access your data. Your conversations are not shared with third parties.

### Can I delete my data?

Yes, you can delete your data by using the /forget command for specific memories or by directly accessing the database file and deleting your records.

## Development and Contribution

### How can I contribute to Jyra?

Check our [Contributing Guide](../CONTRIBUTING.md) and [Community Guide](COMMUNITY.md) for information on how to contribute.

### I found a bug. How do I report it?

Please report bugs on our [GitHub Issues](https://github.com/mosaddiX/jyra/issues) page using the Bug Report template.

### I have an idea for a new feature. How do I suggest it?

You can suggest new features on our [GitHub Issues](https://github.com/mosaddiX/jyra/issues) page using the Feature Request template.

## Still Have Questions?

If your question isn't answered here, please:
- Check our [Documentation](https://github.com/mosaddiX/jyra/tree/main/docs)
- Ask in our [GitHub Discussions](https://github.com/mosaddiX/jyra/discussions)
- Join our [Discord server](https://discord.gg/jyra) for real-time support
