"""
Run migration 005: Fix votes table schema
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def run_migration():
    # Convert URL to use asyncpg driver
    db_url = settings.database_url.replace('postgresql://', 'postgresql+asyncpg://')
    engine = create_async_engine(db_url, echo=True)

    # Split into individual statements
    migration_statements = [
        "SET search_path TO alter_earth",
        "ALTER TABLE votes DROP CONSTRAINT IF EXISTS votes_pkey",
        "ALTER TABLE votes ADD COLUMN IF NOT EXISTS id UUID DEFAULT gen_random_uuid()",
        "UPDATE votes SET id = gen_random_uuid() WHERE id IS NULL",
        "ALTER TABLE votes ADD PRIMARY KEY (id)",
        "ALTER TABLE votes ALTER COLUMN comment_id DROP NOT NULL",
        # Remove duplicate post votes
        """WITH duplicates AS (
            SELECT ctid,
                   ROW_NUMBER() OVER (PARTITION BY user_id, post_id ORDER BY created_at DESC) as rn
            FROM votes
            WHERE post_id IS NOT NULL
        )
        DELETE FROM votes WHERE ctid IN (SELECT ctid FROM duplicates WHERE rn > 1)""",
        # Remove duplicate comment votes
        """WITH duplicates AS (
            SELECT ctid,
                   ROW_NUMBER() OVER (PARTITION BY user_id, comment_id ORDER BY created_at DESC) as rn
            FROM votes
            WHERE comment_id IS NOT NULL
        )
        DELETE FROM votes WHERE ctid IN (SELECT ctid FROM duplicates WHERE rn > 1)""",
        "ALTER TABLE votes ADD CONSTRAINT unique_user_post_vote UNIQUE (user_id, post_id)",
        "ALTER TABLE votes ADD CONSTRAINT unique_user_comment_vote UNIQUE (user_id, comment_id)",
        "CREATE INDEX IF NOT EXISTS idx_votes_post_id ON votes(post_id)",
        "CREATE INDEX IF NOT EXISTS idx_votes_comment_id ON votes(comment_id)",
    ]

    async with engine.begin() as conn:
        for i, stmt in enumerate(migration_statements, 1):
            print(f"\nExecuting statement {i}/{len(migration_statements)}...")
            try:
                await conn.execute(text(stmt))
                print(f"✓ Statement {i} completed")
            except Exception as e:
                print(f"✗ Statement {i} failed: {e}")
                # Continue with other statements even if one fails

        print("\nMigration completed!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_migration())
