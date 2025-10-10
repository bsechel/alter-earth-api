"""
Seed script to create the AlterEarthBot system user.
This bot account will be used for all automated news curation posts.
"""

import asyncio
import uuid
from sqlalchemy import select

from app.core.database import get_async_session, create_async_database_engine
from app.models.user import User, UserType


async def create_alterearth_bot():
    """Create or update the AlterEarthBot system user."""

    # Initialize database engine
    create_async_database_engine()

    # Get database session
    async for session in get_async_session():
        try:
            # Check if bot already exists
            result = await session.execute(
                select(User).where(User.cognito_id == "system_alterearth_bot")
            )
            existing_bot = result.scalar_one_or_none()

            if existing_bot:
                print(f"✓ AlterEarthBot already exists (ID: {existing_bot.id})")
                print(f"  Email: {existing_bot.email}")
                print(f"  Nickname: {existing_bot.nickname}")
                print(f"  User Type: {existing_bot.user_type}")
                return existing_bot

            # Create new bot user
            bot = User(
                id=uuid.uuid4(),
                cognito_id="system_alterearth_bot",
                email="bot@alterearth.com",
                nickname="AlterEarthBot",
                bio="🤖 Automated news curator bringing you the latest environmental and sustainability stories from trusted sources around the world.",
                first_name="AlterEarth",
                last_name="Bot",
                show_real_name=False,
                role="member",
                user_type=UserType.ai_agent,
                is_expert=False,
                is_active=True,
                is_verified=True,  # Bot is pre-verified
                post_count=0,
                comment_count=0,
                vote_count=0,
                post_karma=0,
                comment_karma=0,
            )

            session.add(bot)
            await session.commit()
            await session.refresh(bot)

            print("✅ AlterEarthBot created successfully!")
            print(f"  ID: {bot.id}")
            print(f"  Email: {bot.email}")
            print(f"  Nickname: {bot.nickname}")
            print(f"  User Type: {bot.user_type}")
            print(f"  Cognito ID: {bot.cognito_id}")

            return bot

        except Exception as e:
            print(f"❌ Error creating AlterEarthBot: {e}")
            await session.rollback()
            raise
        finally:
            break  # Exit the async generator loop


async def main():
    """Main execution function."""
    print("Creating AlterEarthBot system user...")
    print("-" * 50)
    await create_alterearth_bot()
    print("-" * 50)
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
