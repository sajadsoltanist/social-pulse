"""Instagram Session Manager - Creates and tests Instagram sessions."""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Optional

# Add app directory to path to import config
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'app'))

from aiograpi import Client
from config import get_config


class InstagramSessionManager:
    """Manages Instagram session creation and validation."""
    
    def __init__(self):
        self.config = get_config()
        self.username = self.config.INSTAGRAM_USERNAME
        self.password = self.config.INSTAGRAM_PASSWORD
        self.session_path = self.config.INSTAGRAM_SESSION_PATH
        
        # Ensure session directory exists
        Path(self.session_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def create_session(self) -> bool:
        """Create a new Instagram session and save it."""
        if not self.username or not self.password:
            print("❌ Instagram credentials not found in environment variables.")
            print("Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD")
            return False
        
        # First, check if existing session is valid
        if os.path.exists(self.session_path):
            print("📂 Found existing session, testing validity...")
            if await self._test_existing_session():
                print("✅ Existing session is valid, no need to create new one!")
                return True
            else:
                print("❌ Existing session is invalid, creating new session...")
        
        try:
            print(f"🔐 Logging into Instagram as {self.username}...")
            
            client = Client()
            
            # Clear old session file if exists
            if os.path.exists(self.session_path):
                print("🗑️  Clearing old session file...")
                os.remove(self.session_path)
            
            # Login with fresh session
            await client.login(self.username, self.password)
            print("✅ Successfully logged into Instagram!")
            
            # Save new session
            client.dump_settings(self.session_path)
            print(f"💾 New session saved to: {self.session_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to create session: {e}")
            return False
    
    async def _test_existing_session(self) -> bool:
        """Test existing session without printing verbose output."""
        try:
            client = Client()
            client.load_settings(self.session_path)
            
            # Try to get profile info to validate session
            await client.user_info_by_username(self.username)
            return True
            
        except Exception:
            return False
    
    async def test_session(self) -> bool:
        """Test if the saved session is working."""
        if not os.path.exists(self.session_path):
            print("❌ No session file found. Please create a session first.")
            return False
        
        try:
            print("🧪 Testing saved session...")
            
            client = Client()
            client.load_settings(self.session_path)
            
            # Test by getting own profile info
            print(f"📊 Getting profile info for {self.username}...")
            user_info = await client.user_info_by_username(self.username)
            
            print("✅ Session is working!")
            print(f"👤 Profile Info:")
            print(f"   - Username: {user_info.username}")
            print(f"   - Full Name: {user_info.full_name}")
            print(f"   - Followers: {user_info.follower_count:,}")
            print(f"   - Following: {user_info.following_count:,}")
            print(f"   - Posts: {user_info.media_count:,}")
            print(f"   - Verified: {'Yes' if user_info.is_verified else 'No'}")
            print(f"   - Private: {'Yes' if user_info.is_private else 'No'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Session test failed: {e}")
            return False
    
    async def session_info(self) -> dict:
        """Get information about the current session."""
        if not os.path.exists(self.session_path):
            return {"exists": False}
        
        try:
            with open(self.session_path, 'r') as f:
                session_data = json.load(f)
            
            file_stat = os.stat(self.session_path)
            
            return {
                "exists": True,
                "path": self.session_path,
                "size": file_stat.st_size,
                "modified": file_stat.st_mtime,
                "username": session_data.get("username", "Unknown"),
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}


async def main():
    """Main function to handle command line interface."""
    manager = InstagramSessionManager()
    
    print("🚀 Instagram Session Manager")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        print("Available commands:")
        print("  create  - Create a new session")
        print("  test    - Test existing session")
        print("  info    - Show session information")
        print()
        command = input("Enter command (create/test/info): ").lower().strip()
    
    if command == "create":
        success = await manager.create_session()
        if success:
            print("\n🎉 Session created successfully!")
            # Automatically test the new session
            print("\n" + "=" * 40)
            await manager.test_session()
        else:
            print("\n💥 Failed to create session!")
            sys.exit(1)
    
    elif command == "test":
        success = await manager.test_session()
        if not success:
            sys.exit(1)
    
    elif command == "info":
        info = await manager.session_info()
        print("📋 Session Information:")
        if info["exists"]:
            if "error" in info:
                print(f"   ❌ Error reading session: {info['error']}")
            else:
                print(f"   📁 Path: {info['path']}")
                print(f"   👤 Username: {info['username']}")
                print(f"   📏 Size: {info['size']} bytes")
                print(f"   🕒 Modified: {info['modified']}")
        else:
            print("   ❌ No session file exists")
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: create, test, info")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 