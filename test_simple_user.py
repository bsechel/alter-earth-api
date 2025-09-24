"""
Simple test to manually create user table and avoid prepared statement issues.
"""

import asyncio
import asyncpg
from app.core.config import settings


async def test_simple_user_creation():
    """Test creating user table manually without SQLAlchemy's automatic creation."""
    print("🔧 Testing simple user table creation...")
    
    try:
        # Connect directly with asyncpg (disable prepared statements for Supabase pooler)
        conn = await asyncpg.connect(
            settings.database_url,
            statement_cache_size=0
        )
        print("✅ Connected to database!")
        
        # Create schema if it doesn't exist
        await conn.execute("CREATE SCHEMA IF NOT EXISTS alter_earth")
        print("✅ Schema 'alter_earth' ensured!")
        
        # Drop table if exists (for clean testing)
        await conn.execute("DROP TABLE IF EXISTS alter_earth.users")
        print("🔄 Dropped existing users table if it existed")
        
        # Create users table manually
        create_table_sql = """
        CREATE TABLE alter_earth.users (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            cognito_id VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            display_name VARCHAR(100) NOT NULL,
            bio TEXT,
            role VARCHAR(20) NOT NULL DEFAULT 'member',
            is_expert BOOLEAN NOT NULL DEFAULT FALSE,
            expertise_areas TEXT,
            institution VARCHAR(200),
            website_url VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            post_count INTEGER NOT NULL DEFAULT 0,
            comment_count INTEGER NOT NULL DEFAULT 0,
            vote_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            last_active_at TIMESTAMP WITH TIME ZONE
        )
        """
        
        await conn.execute(create_table_sql)
        print("✅ Created users table!")
        
        # Create indexes
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_cognito_id ON alter_earth.users(cognito_id)")
        await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON alter_earth.users(email)")
        print("✅ Created indexes!")
        
        # Insert a test user
        insert_sql = """
        INSERT INTO alter_earth.users (cognito_id, email, display_name, bio, role)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, email, display_name, role, created_at
        """
        
        result = await conn.fetchrow(
            insert_sql,
            "test-cognito-123",
            "test@alterearth.com", 
            "Test User",
            "A test user for the Alter Earth platform",
            "member"
        )
        
        print(f"✅ Created test user:")
        print(f"   - ID: {result['id']}")
        print(f"   - Email: {result['email']}")
        print(f"   - Name: {result['display_name']}")
        print(f"   - Role: {result['role']}")
        print(f"   - Created: {result['created_at']}")
        
        # Query the user back
        query_result = await conn.fetchrow(
            "SELECT * FROM alter_earth.users WHERE email = $1",
            "test@alterearth.com"
        )
        
        if query_result:
            print(f"✅ Successfully retrieved user: {query_result['display_name']}")
        
        await conn.close()
        print("\n🎉 Simple user table test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_simple_user_creation())