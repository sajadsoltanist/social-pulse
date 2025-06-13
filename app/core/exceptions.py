class SocialPulseException(Exception):
    """Base exception for SocialPulse application."""
    pass


class UserNotFoundError(SocialPulseException):
    """Raised when a user is not found."""
    pass


class ProfileNotFoundError(SocialPulseException):
    """Raised when a profile is not found."""
    pass


class ProfileAlreadyExistsError(SocialPulseException):
    """Raised when trying to create a profile that already exists."""
    pass


class AlertNotFoundError(SocialPulseException):
    """Raised when an alert is not found."""
    pass


class InvalidCredentialsError(SocialPulseException):
    """Raised when authentication credentials are invalid."""
    pass


class TokenExpiredError(SocialPulseException):
    """Raised when an authentication token has expired."""
    pass


class InstagramServiceError(SocialPulseException):
    """Raised when Instagram service encounters an error."""
    pass


class TelegramServiceError(SocialPulseException):
    """Raised when Telegram service encounters an error."""
    pass 