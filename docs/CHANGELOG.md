# Changelog

All notable changes to the Jyra AI Companion project will be documented in this file.

## [0.5.1] - 2025-04-16

### Fixed
- Added missing get_config function to fix rate limiting middleware

## [0.5.0] - 2025-04-16

### Changed
- Renamed project from "Juno" to "Jyra"
- Updated branding and tagline to "The Soul That Remembers You"
- Enhanced prompt engineering for more emotionally intelligent responses
- Improved documentation to reflect new branding

### Added
- Implemented rate limiting to prevent abuse and ensure fair usage
- Added comprehensive documentation including GETTING_STARTED.md and CONTRIBUTING.md
- Created context middleware for better conversation handling

## [0.4.0] - 2025-04-16

### Added
- Comprehensive test suite with unit and integration tests
- Database optimization with indexes for better performance
- Response caching to reduce API calls and improve response time
- Security check script to identify potential vulnerabilities
- Database optimization script for maintenance

## [0.3.2] - 2025-04-16

### Changed
- Temporarily disabled text-to-speech voice responses due to technical limitations
- Updated settings menu to reflect voice response status
- Maintained speech-to-text functionality for voice messages

## [0.3.1] - 2025-04-16

### Added
- Integrated FFmpeg for audio processing
- Bundled FFmpeg binaries with the application
- Improved audio conversion reliability

## [0.3.0] - 2025-04-16

### Added
- Multi-modal support for images and voice messages
- Image processing with detailed descriptions
- Speech-to-text conversion for voice messages
- Text-to-speech capabilities for voice responses
- New /voice command to toggle voice responses
- Voice response setting in user preferences

### Changed
- Updated help command to include multi-modal features
- Enhanced settings menu with voice response toggle
- Improved message handlers to process photos and voice messages

## [0.2.0] - 2025-04-16

### Added
- Sentiment analysis to detect user's emotional state
- Emotion-based response adjustment for more empathetic interactions
- New /mood command to display emotional trends
- Visualization of emotional patterns over time
- Emotional context added to AI prompts

### Changed
- Updated help command to include the new /mood command
- Enhanced message handling to incorporate sentiment analysis
- Improved AI response generation with emotional awareness

## [0.1.3] - 2025-04-16

### Fixed
- Completely rewrote Gemini API integration to use direct API calls
- Implemented the exact API format from the curl example
- Added detailed error logging for API responses
- Fixed the "I'm having trouble connecting to my AI brain" error

## [0.1.2] - 2025-04-16

### Fixed
- Fixed Gemini API integration to properly handle responses
- Updated to use Gemini 1.5 Flash model for better performance and reliability
- Improved error handling for API connection issues

## [0.1.1] - 2025-04-16

### Added
- Cancel button for role creation process
- Improved Gemini model integration with proper safety settings
- Enhanced chat session handling for better conversation context

### Fixed
- Role creation process can now be cancelled at any step
- Improved error handling in AI response generation
- Better prompt formatting for more consistent responses

## [0.1.0] - 2025-04-16

### Added
- Initial project structure and architecture
- Comprehensive documentation (README, ROADMAP, ARCHITECTURE, USER_GUIDE, DEVELOPMENT_GUIDE)
- Basic bot framework with command handling
- Database models for users, roles, conversations, and memories
- Role management system with 8 predefined roles
- Custom role creation functionality
- Conversation history storage
- Memory system for storing important user information
- User preferences system
- AI integration with Google Gemini
- Command handlers for all basic functionality
- Callback query handlers for interactive menus
- Error handling and logging system

### Fixed
- Event loop initialization issue in main thread by using nest_asyncio
- Terminal output enhanced with colors and progress indicators

### Pending
- Testing suite
- Production deployment
