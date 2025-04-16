# Deployment Guide for Jyra AI Companion

This guide explains how to deploy Jyra to Railway.app for free 24/7 hosting.

## Prerequisites

- A Railway.app account (sign up at https://railway.app/)
- A GitHub account (for connecting to Railway)
- Your Telegram Bot Token (from BotFather)
- Your Google Gemini API key

## Deployment Steps

### 1. Fork the Repository

1. Fork the Jyra repository to your GitHub account
2. Clone your forked repository to your local machine

### 2. Set Up Railway

1. Log in to Railway.app with your GitHub account
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your forked Jyra repository
5. Railway will automatically detect the configuration from railway.toml

### 3. Configure Environment Variables

Add the following environment variables in the Railway dashboard:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `GEMINI_API_KEY`: Your Google Gemini API key
- `PORT`: 8080 (or any port you prefer)

### 4. Deploy the Project

1. Railway will automatically deploy your project
2. Monitor the deployment logs for any errors
3. Once deployed, your bot will be running 24/7

## Maintaining Your Deployment

### Updating Your Bot

When you want to update your bot:

1. Push changes to your GitHub repository
2. Railway will automatically redeploy your bot

### Monitoring

1. Use the Railway dashboard to monitor your bot's performance
2. Check logs for any errors or issues
3. Set up notifications for deployment failures

### Free Tier Limitations

Railway's free tier includes:
- 500 hours of runtime per month
- 5 projects
- 1GB of RAM
- 1 vCPU

If you need more resources, consider upgrading to a paid plan.

## Troubleshooting

### Common Issues

1. **Bot not responding**: Check the logs for errors and ensure your Telegram token is correct
2. **Deployment failing**: Verify that all dependencies are properly listed in requirements.txt
3. **Database errors**: Make sure the SQLite database file is being created in a writable directory

### Getting Help

If you encounter issues with your deployment:
1. Check the Railway documentation: https://docs.railway.app/
2. Join the Railway Discord community for support
3. Open an issue in the Jyra GitHub repository

## Alternative Deployment Options

If Railway doesn't meet your needs, consider these alternatives:

1. **Render.com**: Similar to Railway with a free tier
2. **PythonAnywhere**: Good for Python applications with a free tier
3. **Fly.io**: Container-based hosting with a generous free tier
4. **Heroku**: Paid option with more features and scalability
