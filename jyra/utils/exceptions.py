"""
Custom exceptions for Jyra bot.

This module defines custom exception classes for different types of errors
that can occur in the Jyra bot. Using custom exceptions makes error handling
more consistent and provides better context for debugging.
"""

class JyraException(Exception):
    """Base exception class for all Jyra-specific exceptions."""
    
    def __init__(self, message: str = "An error occurred in Jyra", details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


# Database Exceptions
class DatabaseException(JyraException):
    """Base exception for database-related errors."""
    
    def __init__(self, message: str = "Database error", details: str = None):
        super().__init__(message, details)


class DatabaseConnectionError(DatabaseException):
    """Exception raised when there's an error connecting to the database."""
    
    def __init__(self, details: str = None):
        super().__init__("Failed to connect to database", details)


class DatabaseQueryError(DatabaseException):
    """Exception raised when there's an error executing a database query."""
    
    def __init__(self, query: str = None, details: str = None):
        message = "Failed to execute database query"
        if query:
            details = f"Query: {query}" + (f" - {details}" if details else "")
        super().__init__(message, details)


class DatabaseIntegrityError(DatabaseException):
    """Exception raised when there's a database integrity error."""
    
    def __init__(self, details: str = None):
        super().__init__("Database integrity error", details)


# API Exceptions
class APIException(JyraException):
    """Base exception for API-related errors."""
    
    def __init__(self, message: str = "API error", details: str = None):
        super().__init__(message, details)


class AIModelException(APIException):
    """Exception raised when there's an error with the AI model."""
    
    def __init__(self, model: str = None, details: str = None):
        message = "AI model error"
        if model:
            message = f"Error with AI model: {model}"
        super().__init__(message, details)


class APIRateLimitException(APIException):
    """Exception raised when an API rate limit is reached."""
    
    def __init__(self, api: str = None, details: str = None):
        message = "API rate limit reached"
        if api:
            message = f"Rate limit reached for API: {api}"
        super().__init__(message, details)


class APIAuthenticationException(APIException):
    """Exception raised when there's an authentication error with an API."""
    
    def __init__(self, api: str = None, details: str = None):
        message = "API authentication error"
        if api:
            message = f"Authentication error for API: {api}"
        super().__init__(message, details)


# User Input Exceptions
class UserInputException(JyraException):
    """Base exception for user input-related errors."""
    
    def __init__(self, message: str = "Invalid user input", details: str = None):
        super().__init__(message, details)


class InvalidCommandException(UserInputException):
    """Exception raised when a user provides an invalid command."""
    
    def __init__(self, command: str = None, details: str = None):
        message = "Invalid command"
        if command:
            message = f"Invalid command: {command}"
        super().__init__(message, details)


class ValidationException(UserInputException):
    """Exception raised when user input fails validation."""
    
    def __init__(self, field: str = None, details: str = None):
        message = "Input validation failed"
        if field:
            message = f"Validation failed for field: {field}"
        super().__init__(message, details)


# Configuration Exceptions
class ConfigException(JyraException):
    """Base exception for configuration-related errors."""
    
    def __init__(self, message: str = "Configuration error", details: str = None):
        super().__init__(message, details)


class MissingConfigException(ConfigException):
    """Exception raised when a required configuration is missing."""
    
    def __init__(self, config_key: str = None, details: str = None):
        message = "Missing required configuration"
        if config_key:
            message = f"Missing required configuration: {config_key}"
        super().__init__(message, details)


class InvalidConfigException(ConfigException):
    """Exception raised when a configuration value is invalid."""
    
    def __init__(self, config_key: str = None, details: str = None):
        message = "Invalid configuration value"
        if config_key:
            message = f"Invalid configuration value for: {config_key}"
        super().__init__(message, details)


# Feature Exceptions
class FeatureException(JyraException):
    """Base exception for feature-related errors."""
    
    def __init__(self, message: str = "Feature error", details: str = None):
        super().__init__(message, details)


class FeatureNotImplementedException(FeatureException):
    """Exception raised when a requested feature is not implemented."""
    
    def __init__(self, feature: str = None, details: str = None):
        message = "Feature not implemented"
        if feature:
            message = f"Feature not implemented: {feature}"
        super().__init__(message, details)


class FeatureDisabledException(FeatureException):
    """Exception raised when a requested feature is disabled."""
    
    def __init__(self, feature: str = None, details: str = None):
        message = "Feature is disabled"
        if feature:
            message = f"Feature is disabled: {feature}"
        super().__init__(message, details)


# Permission Exceptions
class PermissionException(JyraException):
    """Base exception for permission-related errors."""
    
    def __init__(self, message: str = "Permission error", details: str = None):
        super().__init__(message, details)


class UnauthorizedException(PermissionException):
    """Exception raised when a user is not authorized to perform an action."""
    
    def __init__(self, action: str = None, details: str = None):
        message = "Unauthorized action"
        if action:
            message = f"Unauthorized action: {action}"
        super().__init__(message, details)


class RateLimitedException(PermissionException):
    """Exception raised when a user has been rate limited."""
    
    def __init__(self, action: str = None, details: str = None):
        message = "Rate limited"
        if action:
            message = f"Rate limited for action: {action}"
        super().__init__(message, details)
