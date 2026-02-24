# MEMORY.md Structure Template

This template shows the recommended structure for MEMORY.md.
Claude should adapt this to each project's needs.

## Good Example

```
# Project Memory

## Active Work
- **Implement user auth**
  Status: 70% done — JWT middleware complete, refresh token logic pending
  Context: Stateless auth required for horizontal scaling; sessions rejected early
  Decisions: jsonwebtoken over passport-jwt (simpler API, fewer deps)
  Modified: src/middleware/auth.js, src/routes/auth.js
  Next: add refresh token endpoint and rotation logic
  See: auth-design.md

- **Fix CI pipeline**
  Status: Investigating Node version mismatch between local (20) and CI (18)
  Context: Tests pass locally but fail on GitHub Actions with ESM import errors
  Next: pin Node version in .github/workflows/ci.yml to 20

## Project Overview
- Express.js REST API with PostgreSQL
- Key dirs: src/routes/, src/middleware/, src/models/
- Build: `npm run build` | Test: `npm test` | Lint: `npm run lint`

## Decisions & Conventions
- JWT for auth (not sessions): stateless scaling requirement; express-session rejected due to horizontal scaling constraints
- Snake_case for DB columns, camelCase for JS variables: matches ORM convention
- All API responses use { data, error, meta } envelope: decided in v1 design, enforced in src/middleware/response.js

## Resolved Issues
- Login 500 error → missing DATABASE_URL env var → added to .env.example and documented in README setup section
- Test timeout → jest default 5s too short for DB tests (connection pool spin-up) → set testTimeout to 15s in jest.config

## User Preferences
- Prefers concise explanations, minimal boilerplate
- Uses Gitmoji + Korean commit messages
- Wants tests written alongside implementation, not after

## Topic File Index
- auth-design.md: JWT auth architecture, token flow, middleware chain
- debugging.md: Active debugging notes for CI pipeline issue
```

## Bad Example (What NOT to Do)

```
# Memory

Talked to user about auth. They want JWT. Tried sessions first but
didn't work well. Spent 2 hours debugging the middleware. Found that
express-session was conflicting with cors. Eventually switched to
jsonwebtoken library. The user seemed happy with this approach.

Also the tests were failing because of some timeout issue I think
maybe related to the database connection pool being exhausted but
I'm not sure yet. Will look into it more later.

The user likes short answers. They also use some Korean in their
commit messages with emoji things.
```

Problems with the bad example:
- Narrative style wastes lines (not structured and concise)
- Contains debugging journey (should only record the solution)
- Includes speculation ("I think maybe")
- No structure for quick scanning
- No Active Work section (no recovery anchor)
- Missing key details (files modified, alternatives rejected, blockers)
- No topic file references
