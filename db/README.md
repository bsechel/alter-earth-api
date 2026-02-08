# Database Migrations & Seeds

This directory contains SQL migrations and seed data scripts for the Alter Earth API database.

## Directory Structure

```
db/
├── migrations/     # SQL migration files (applied in order)
├── seeds/          # Seed data scripts (Python)
└── README.md       # This file
```

## Migrations

Migrations are numbered SQL files that should be applied in order.

### Current Migrations

1. **001_add_user_karma_and_type.sql** - Adds karma and user_type fields to users table
   - Adds `user_type` ENUM ('human', 'ai_agent')
   - Adds `post_karma` and `comment_karma` INTEGER fields
   - Creates indexes for performance

### Running Migrations

#### Option 1: Using Supabase MCP (Recommended)
Once you add Supabase MCP, you can run migrations through it.

#### Option 2: Using psql
```bash
psql $DATABASE_URL -f db/migrations/001_add_user_karma_and_type.sql
```

#### Option 3: Using Supabase Dashboard
1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Copy and paste the migration SQL
4. Execute

## Seed Data

Seed scripts are Python files that populate initial data.

### Current Seeds

1. **create_alterearth_bot.py** - Creates the AlterEarthBot system user

### Running Seed Scripts

```bash
# Activate virtual environment
source venv/bin/activate

# Run seed script
python db/seeds/create_alterearth_bot.py
```

## Phase 2 Migration Plan

The following migrations will be created as part of Phase 2:

1. ✅ `001_add_user_karma_and_type.sql` - User table updates
2. ⏳ `002_create_posts_table.sql` - Core posts table
3. ⏳ `003_create_automated_articles.sql` - Automated articles detail table
4. ⏳ `004_create_user_submissions.sql` - User submissions detail table
5. ⏳ `005_create_votes_table.sql` - Voting system
6. ⏳ `006_create_comments_table.sql` - Comments with threading
7. ⏳ `007_add_indexes.sql` - Performance indexes
8. ⏳ `008_migrate_news_articles.sql` - Data migration from old schema

## Notes

- Always backup your database before running migrations
- Migrations should be idempotent (safe to run multiple times)
- Use `IF NOT EXISTS` and `IF EXISTS` clauses where appropriate
- Test migrations on development environment first
