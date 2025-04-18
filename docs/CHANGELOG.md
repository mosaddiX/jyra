# Changelog

All notable changes to the Jyra AI Companion project will be documented in this file.

## [Unreleased]

### Added
- **Database Initialization**: Added scripts and logic to create all required tables (`roles`, `users`, `memories`) automatically.
- **Role Model Enhancements**: Added `is_featured` and `is_popular` fields to the `roles` table and model for advanced UI filtering.
- **Featured/Popular Roles UI**: Role selection menu now supports "🌟 Featured" and "🔥 Popular" sections with filter buttons and emoji indicators.
- **Automatic Featured Refresh**: Featured roles are now randomly refreshed daily, triggered on the first role menu access each day (no manual scripts required).
- **Robust Migration Handling**: Migration scripts safely handle missing or duplicate columns.

### Changed
- **Role Selection UI**: Improved with visual indicators, filter buttons, and clear navigation for a more user-friendly experience.
- **Bot Initialization**: Ensured default roles are initialized on first use if the roles table is empty.

### Removed
- Removed standalone script for featuring roles; all logic is now handled internally and automatically by the bot.


## [1.0.0] - 2025-04-17 (Final Release)

### Added
- Final release of Jyra AI Companion
- Complete implementation of all planned features

### Changed
- Simplified community engagement system for better reliability
- Removed priority selection from support tickets to streamline the process
- Improved error handling in community engagement features
- Updated roadmap to mark project as complete

### Fixed
- Fixed issues with callback handlers in community engagement system
- Removed unused code and files to clean up the codebase

## [0.7.0] - 2025-04-16

### Added
- Comprehensive community engagement system
- Feedback collection mechanism with rating system
- Feature request system with voting capabilities
- Support ticket system with priority levels
- Community documentation and guidelines
- GitHub issue templates for bug reports, feature requests, and feedback
- Contributors recognition system

## [0.6.1] - 2025-04-16

### Fixed
- Fixed sentiment variable access bug in message handler
- Fixed memory extractor by adding required role_context parameter
- Cleaned up unused imports

## [0.6.0] - 2025-04-16

### Added
- Enhanced memory system with categories, importance levels, and context
- Automatic memory extraction from user messages using AI
- Memory summaries for long-term memory retention
- Improved memory retrieval based on conversation context and sentiment
- Increased conversation history limit from 10 to 50 messages

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
