import os
import asyncio
import logging
from typing import Optional
from pathlib import Path

from aiograpi import Client
from aiograpi.exceptions import LoginRequired, UserNotFound, PleaseWaitFewMinutes

from app.core.interfaces import InstagramService
from app.core.exceptions import InstagramServiceError
from app.config import get_config

logger = logging.getLogger(__name__)


class InstagramClientImpl(InstagramService):
    def __init__(self):
        self.config = get_config()
        self.client: Optional[Client] = None
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize Instagram client with session management"""
        try:
            # Initialize client without any extra parameters
            self.client = Client()
            
            # Set delay range after initialization
            if hasattr(self.client, 'delay_range'):
                self.client.delay_range = self.config.MONITORING_DELAY_RANGE
            
            # Ensure data directory exists
            session_path = Path(self.config.INSTAGRAM_SESSION_PATH)
            session_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Only try to load existing session - no automatic login
            if self._load_session():
                logger.info("Loaded existing Instagram session")
                if await self._validate_session():
                    self._initialized = True
                    return True
                else:
                    logger.error("Session invalid. Please run 'python instagram_login.py' to login manually")
            else:
                logger.error("No Instagram session found. Please run 'python instagram_login.py' to login manually")
                
            return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Instagram client: {e}")
            return False
    
    async def get_follower_count(self, username: str) -> Optional[int]:
        """Get follower count for a username"""
        if not await self._ensure_authenticated():
            raise InstagramServiceError("Instagram client not authenticated")
            
        try:
            return await self._with_retry(
                lambda: self._get_user_follower_count(username)
            )
        except UserNotFound:
            logger.warning(f"Instagram user not found: {username}")
            return None
        except Exception as e:
            logger.error(f"Error getting follower count for {username}: {e}")
            raise InstagramServiceError(f"Failed to get follower count: {str(e)}")
    
    async def _get_user_follower_count(self, username: str) -> int:
        """Internal method to get follower count"""
        user_info = await self.client.user_info_by_username(username)
        return user_info.follower_count
    
    async def _ensure_authenticated(self) -> bool:
        """Ensure client is authenticated and ready"""
        if not self._initialized:
            return await self.initialize()
            
        try:
            # Quick validation check
            await self.client.get_timeline_feed()
            return True
        except LoginRequired:
            logger.error("Session expired. Please run 'python instagram_login.py' to login again")
            return False
        except Exception as e:
            logger.error(f"Authentication check failed: {e}")
            return False
    
    async def _validate_session(self) -> bool:
        """Validate current session"""
        try:
            await self.client.get_timeline_feed()
            return True
        except LoginRequired:
            return False
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False
    
    def _load_session(self) -> bool:
        """Load session from file"""
        try:
            session_path = self.config.INSTAGRAM_SESSION_PATH
            if os.path.exists(session_path):
                session = self.client.load_settings(session_path)
                if session:
                    self.client.set_settings(session)
                    return True
            return False
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return False
    
    def _save_session(self) -> None:
        """Save session to file"""
        try:
            session_path = self.config.INSTAGRAM_SESSION_PATH
            self.client.dump_settings(session_path)
            
            # Set secure permissions (600)
            os.chmod(session_path, 0o600)
            logger.info("Instagram session saved")
        except Exception as e:
            logger.error(f"Error saving session: {e}")
    
    async def _fresh_login(self) -> bool:
        """Perform fresh login"""
        try:
            if not self.config.INSTAGRAM_USERNAME or not self.config.INSTAGRAM_PASSWORD:
                logger.error("Instagram credentials not configured")
                return False
            
            # Preserve UUIDs if we have them
            old_session = self.client.get_settings() if self.client else {}
            if old_session and 'uuids' in old_session:
                self.client.set_settings({})
                self.client.set_uuids(old_session['uuids'])
            
            success = await self.client.login(
                self.config.INSTAGRAM_USERNAME,
                self.config.INSTAGRAM_PASSWORD
            )
            
            if success:
                logger.info("Instagram login successful")
                return True
            else:
                logger.error("Instagram login failed")
                return False
                
        except Exception as e:
            logger.error(f"Fresh login failed: {e}")
            return False
    
    async def _with_retry(self, operation, max_retries: int = 3):
        """Execute operation with retry logic"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await operation()
            except PleaseWaitFewMinutes as e:
                wait_time = min(60 * (2 ** attempt), 300)  # Exponential backoff, max 5 min
                logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1})")
                await asyncio.sleep(wait_time)
                last_exception = e
            except LoginRequired:
                logger.info("Login required during operation, re-authenticating")
                if await self._fresh_login():
                    self._save_session()
                    continue
                else:
                    raise InstagramServiceError("Re-authentication failed")
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = 2 ** attempt
                logger.warning(f"Operation failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                last_exception = e
        
        raise last_exception or InstagramServiceError("Max retries exceeded")
