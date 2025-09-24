"""
Test script to verify User model and database connection.
"""

import asyncio
from app.core.database import create_async_database_engine, init_db, get_async_session
from app.models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def test_user_model():
    """Test creating and querying a user."""
    print("🔧 Testing User model and database connection...")
    
    try:
        # Initialize database and create tables
        print("📦 Creating database tables...")
        await init_db()
        print("✅ Tables created successfully!")
        
        # Test creating a user
        print("👤 Creating test user...")
        async for session in get_async_session():
            # Create a test user
            test_user = User(
                cognito_id="test-cognito-123",
                email="test@alterearth.com", 
                display_name="Test User",
                bio="A test user for the Alter Earth platform",
                role="member"
            )
            
            session.add(test_user)
            await session.commit()
            print(f"✅ Created user: {test_user}")
            
            # Query the user back
            from sqlalchemy import select
            result = await session.execute(select(User).where(User.email == "test@alterearth.com"))
            retrieved_user = result.scalars().first()
            
            if retrieved_user:
                print(f"✅ Retrieved user: {retrieved_user}")
                print(f"   - ID: {retrieved_user.id}")
                print(f"   - Cognito ID: {retrieved_user.cognito_id}")
                print(f"   - Email: {retrieved_user.email}")
                print(f"   - Role: {retrieved_user.role}")
                print(f"   - Created: {retrieved_user.created_at}")
            else:
                print("❌ Failed to retrieve user")
            
            break  # Only test with first session
            
        print("\n🎉 User model test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error testing user model: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_user_model())