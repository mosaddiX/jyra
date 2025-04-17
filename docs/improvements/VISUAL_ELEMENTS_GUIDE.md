# Visual Elements Guide for Jyra Bot

This guide explains how to use visual elements (stickers, animations, images) in your Jyra bot.

## Overview

The Jyra bot uses three types of visual elements:

1. **Stickers**: Telegram stickers for emotional responses
2. **Animations**: GIFs for interactive elements and loading states
3. **Images**: Static images for rich content and illustrations

These elements are managed through the `jyra/ui/visual_elements.py` module.

## Setting Up Visual Elements

Before using visual elements, you need to:

1. **Download assets** using the `download_assets.py` script
2. **Create a sticker pack** following the instructions in `STICKER_SETUP_GUIDE.md`
3. **Get file_ids** for your stickers and animations
4. **Update the IDs** in `jyra/ui/visual_elements.py`

## Using Stickers

Stickers are great for emotional responses and can make your bot feel more alive.

### When to Use Stickers

- **Greetings**: Welcome new users
- **Emotional responses**: React to user sentiment
- **Celebrations**: Acknowledge achievements
- **Transitions**: Mark the beginning or end of a conversation

### Code Example

```python
from jyra.ui.visual_elements import send_sticker

# In a command handler
async def handle_greeting(update, context):
    # Send a welcome sticker
    await send_sticker(update, context, "welcome")
    
    # Then send your text message
    await update.message.reply_text("Hello! How can I help you today?")
```

## Using Animations

Animations (GIFs) are useful for showing progress, transitions, or adding visual interest.

### When to Use Animations

- **Loading states**: Show the bot is processing
- **Tutorials**: Demonstrate features
- **Transitions**: Move between different states
- **Celebrations**: Mark achievements or milestones

### Code Example

```python
from jyra.ui.visual_elements import send_animation

# In a command handler
async def handle_processing(update, context):
    # Send a processing animation
    await send_animation(
        update, 
        context, 
        "processing",
        caption="I'm analyzing your request..."
    )
    
    # Process the request
    result = await process_request()
    
    # Send the result
    await update.message.reply_text(f"Here's what I found: {result}")
```

## Using Images

Images are useful for rich content, illustrations, and visual explanations.

### When to Use Images

- **Onboarding**: Introduce features with illustrations
- **Help sections**: Visualize concepts
- **Results**: Show data visualizations
- **Explanations**: Illustrate complex ideas

### Code Example

```python
from jyra.ui.visual_elements import send_image

# In a command handler
async def handle_help(update, context):
    # Send a help image with caption
    await send_image(
        update, 
        context, 
        "help",
        caption="Here's how to use the main features:"
    )
    
    # Send additional text if needed
    await update.message.reply_text("Type /start to begin!")
```

## Best Practices

1. **Don't overuse visual elements** - They should enhance the experience, not distract from it
2. **Ensure accessibility** - Always provide text alternatives
3. **Be consistent** - Use the same visual language throughout
4. **Consider performance** - Large files can slow down the experience
5. **Test on different devices** - Ensure visuals look good on all screen sizes

## Customizing Visual Elements for Different Themes

The visual elements can be customized based on the user's selected theme:

```python
from jyra.ui.themes import get_current_theme
from jyra.ui.visual_elements import send_sticker, get_emotion_emoji

# In a command handler
async def handle_emotion(update, context, emotion):
    # Get current theme
    theme = get_current_theme()
    
    # Get theme-specific emoji
    emoji = theme.get_property("primary_emoji")
    if theme.get_property("use_emojis"):
        emoji = get_emotion_emoji(emotion)
    
    # Send appropriate sticker
    if theme.get_property("sticker_style") == "auto":
        await send_sticker(update, context, emotion)
    
    # Send text with theme-specific formatting
    message = f"{emoji} I'm feeling {emotion}!"
    await update.message.reply_text(message)
```

## Troubleshooting

- **Missing assets**: Run the `download_assets.py` script again
- **Sticker not sending**: Verify the file_id is correct
- **Animation too large**: Optimize your GIFs to be under 1MB
- **Image quality issues**: Ensure images are properly sized and compressed
