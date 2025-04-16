# Testing Instructions for Jyra's Sentiment Analysis

## Overview
This document provides instructions for testing the sentiment analysis feature in Jyra.

## Test Cases

### 1. Basic Sentiment Detection
Send the following messages to the bot and observe how it responds:

- **Happy/Positive**: "I'm so excited about this new feature! It's amazing!"
- **Sad/Negative**: "I'm feeling really down today, nothing seems to be going right."
- **Angry**: "This is so frustrating! I can't believe it's not working!"
- **Anxious**: "I'm really worried about my upcoming presentation."
- **Neutral**: "The weather is cloudy with a chance of rain."
- **Confused**: "I'm not sure I understand how this works."

### 2. Testing the /mood Command
1. Send several messages with different emotional tones
2. Use the `/mood` command to see your emotional trends
3. Verify that the bot correctly displays:
   - Your current mood
   - Most frequent emotion
   - Emotional distribution
   - (Possibly) A visualization of your emotional trends

### 3. Response Adaptation
Send messages with different emotional tones and observe how the bot's responses adapt:

1. For positive emotions: Does the bot match your energy and enthusiasm?
2. For negative emotions: Does the bot respond with empathy and support?
3. For confusion: Does the bot provide clearer explanations?
4. For neutral messages: Does the bot maintain a balanced tone?

## Expected Results

1. **Sentiment Detection**: The bot should correctly identify the primary emotion in your messages.
2. **Response Adaptation**: The bot's responses should adapt to your emotional state.
3. **Mood Command**: The `/mood` command should provide accurate insights about your emotional trends.

## Reporting Issues
If you encounter any issues during testing, please note:
- The specific message you sent
- The expected response
- The actual response
- Any error messages or unexpected behavior
