"""
Simple database connection test.
"""

import asyncio
import asyncpg
from app.core.config import settings


async def test_basic_connection():
    """Test basic database connection without SQLAlchemy."""
    print("🔧 Testing basic database connection...")
    print(f"📡 Connecting to: {settings.database_url}")
    
    try:
        # Convert to asyncpg format
        db_url = settings.database_url.replace("postgresql://", "postgresql://")
        
        # Test basic connection
        conn = await asyncpg.connect(db_url)
        print("✅ Connected to database successfully!")
        
        # Test simple query
        result = await conn.fetchval("SELECT version()")
        print(f"✅ PostgreSQL version: {result}")
        
        await conn.close()
        print("✅ Connection test completed!")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"❌ Database URL: {settings.database_url}")
        raise

if __name__ == "__main__":
    asyncio.run(test_basic_connection())