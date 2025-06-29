import logging
from typing import Optional
from datetime import datetime, timezone
from telegram import Bot
from telegram.request import HTTPXRequest
from telegram.error import TelegramError, InvalidToken, NetworkError

from app.core.interfaces import TelegramService
from app.core.exceptions import TelegramServiceError
from app.config import Config

logger = logging.getLogger(__name__)


class TelegramClientImpl(TelegramService):
    def __init__(self, config: Config):
        self.config = config
        self.bot_token = config.TELEGRAM_BOT_TOKEN
        self._bot: Optional[Bot] = None
        
    @property
    def bot(self) -> Bot:
        """Lazy initialization of Bot instance"""
        if self._bot is None:
            if not self.bot_token:
                raise TelegramServiceError("Telegram bot token not configured")
            
            # Use HTTPXRequest with proper configuration
            request = HTTPXRequest(
                connection_pool_size=8,
                read_timeout=30,
                write_timeout=30,
                connect_timeout=30,
                pool_timeout=30
            )
            
            self._bot = Bot(token=self.bot_token, request=request)
        return self._bot

    async def send_milestone_alert(self, chat_id: str, username: str, threshold: int, current_count: int) -> bool:
        """Send milestone achievement notification"""
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
            return False
        
        try:
            message = self._format_milestone_message(username, threshold, current_count)
            return await self.send_message(chat_id, message)
        except Exception as e:
            logger.error(f"Failed to send milestone alert: {e}")
            return False

    async def send_message(self, chat_id: str, message: str) -> bool:
        """Send a message to a Telegram chat"""
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='HTML'
            )
            logger.info(f"Message sent successfully to chat {chat_id}")
            return True
            
        except InvalidToken:
            logger.error("Invalid Telegram bot token")
            return False
        except NetworkError as e:
            logger.error(f"Network error sending Telegram message: {e}")
            return False
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram message: {e}")
            return False

    def _format_milestone_message(self, username: str, threshold: int, current_count: int) -> str:
        """Format milestone achievement message"""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        return f"""🎉 <b>Milestone Achieved!</b>

Your Instagram account <b>@{username}</b> has reached <b>{threshold:,}</b> followers!

📊 Current count: <b>{current_count:,}</b> followers
⏰ Achieved at: {timestamp}
"""

    async def validate_bot_token(self) -> bool:
        """Validate bot token by calling getMe API"""
        if not self.bot_token:
            logger.error("Telegram bot token not configured")
            return False
        
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Bot validated: @{bot_info.username}")
            return True
            
        except InvalidToken:
            logger.error("Invalid Telegram bot token")
            return False
        except NetworkError as e:
            logger.error(f"Network error validating bot token: {e}")
            return False
        except TelegramError as e:
            logger.error(f"Telegram API error validating bot token: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error validating bot token: {e}")
            return False

    async def get_chat_info(self, chat_id: str) -> Optional[dict]:
        """Get information about a chat"""
        try:
            chat = await self.bot.get_chat(chat_id=chat_id)
            return {
                "id": chat.id,
                "type": chat.type,
                "title": getattr(chat, 'title', None),
                "username": getattr(chat, 'username', None),
                "first_name": getattr(chat, 'first_name', None),
                "last_name": getattr(chat, 'last_name', None)
            }
        except TelegramError as e:
            logger.error(f"Error getting chat info for {chat_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting chat info: {e}")
            return None

    async def close(self):
        """Close the underlying HTTP client"""
        if self._bot and hasattr(self._bot, '_request') and self._bot._request:
            try:
                if hasattr(self._bot._request, 'shutdown'):
                    await self._bot._request.shutdown()
                elif hasattr(self._bot._request, 'close'):
                    await self._bot._request.close()
            except Exception as e:
                logger.error(f"Error closing Telegram HTTP client: {e}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
