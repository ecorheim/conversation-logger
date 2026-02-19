# MEMORY.md Structure Template

This template shows the recommended structure for MEMORY.md.
Claude should adapt this to each project's needs.

## Good Example

```
# Project Memory

## Active Work
- Implement user auth | 70% done, JWT middleware complete | Next: add refresh token logic | See: auth-design.md
- Fix CI pipeline | Investigating | Next: check Node version mismatch | See: debugging.md

## Project Overview
- Express.js REST API with PostgreSQL
- Key dirs: src/routes/, src/middleware/, src/models/
- Build: `npm run build` | Test: `npm test` | Lint: `npm run lint`

## Decisions & Conventions
- JWT for auth (not sessions) — stateless scaling requirement
- Snake_case for DB columns, camelCase for JS variables
- All API responses use { data, error, meta } envelope

## Resolved Issues
- Login 500 error → missing DATABASE_URL env var → added to .env.example
- Test timeout → jest default 5s too short for DB tests → set to 15s in jest.config

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
- Narrative style wastes lines (not semantically compressed)
- Contains debugging journey (should only record the solution)
- Includes speculation ("I think maybe")
- No structure for quick scanning
- No Active Work section (no recovery anchor)
- No topic file references
