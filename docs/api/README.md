# Alter Earth API Documentation

This directory contains versioned OpenAPI specifications for the Alter Earth API.

## Versioned Specs

- **`openapi-v1-phase2.json`** - Phase 2 complete (Posts, Comments, Voting system)
  - Date: 2025-10-10
  - Features: Unified post system, Reddit-style voting, threaded comments, karma, hot/top/new sorting

## Live API Documentation

When the server is running, you can access:

- **Interactive Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Generating New Snapshots

To create a new versioned snapshot:

```bash
# Start the server
uvicorn main:app --reload

# In another terminal, fetch the spec
curl http://localhost:8000/openapi.json > docs/api/openapi-v1-phaseN.json

# Commit it
git add docs/api/openapi-v1-phaseN.json
git commit -m "Add OpenAPI spec for Phase N"
```

## Using the Spec

### With Frontend Development

```bash
# Generate TypeScript types
npx openapi-typescript docs/api/openapi-v1-phase2.json --output src/types/api.ts

# Generate API client
npx @openapitools/openapi-generator-cli generate \
  -i docs/api/openapi-v1-phase2.json \
  -g typescript-fetch \
  -o src/api
```

### With Postman

Import `docs/api/openapi-v1-phase2.json` directly into Postman to get all endpoints with proper request/response schemas.

## API Versioning Strategy

- Major versions (v1, v2) indicate breaking changes
- Phase snapshots track feature evolution within a version
- The live `/openapi.json` endpoint always reflects the current state
- Committed snapshots provide historical reference and stable contracts for frontend

## Endpoints by Feature

### Phase 2 (Current)

**Posts**
- `GET /api/v1/posts` - List posts with sorting (hot, top, new, controversial, rising)
- `GET /api/v1/posts/{id}` - Get single post
- `POST /api/v1/posts` - Create user submission

**Comments**
- `POST /api/v1/comments` - Create comment/reply
- `GET /api/v1/comments/post/{post_id}` - Get comment tree
- `GET /api/v1/comments/{id}` - Get single comment
- `PUT /api/v1/comments/{id}` - Update comment
- `DELETE /api/v1/comments/{id}` - Delete comment (soft delete)

**Voting**
- `POST /api/v1/votes/posts/{id}` - Vote on post
- `DELETE /api/v1/votes/posts/{id}` - Remove vote from post
- `GET /api/v1/votes/posts/{id}/status` - Check user's vote on post
- `POST /api/v1/votes/comments/{id}` - Vote on comment
- `GET /api/v1/votes/comments/{id}/status` - Check user's vote on comment

**Users**
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile

**Auth**
- `POST /api/v1/auth/callback` - OAuth callback (Google, AWS Cognito)
