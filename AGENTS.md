# Rowing Proj — Agent Instructions

## Project Identity
We are building a rowing training app that aggregates workout data from manual entry, Concept2, and Strava, then visualizes progress. Users have private profiles and can join teams that share data.

## Core Goals (MVP)
- Manual workout logging form with validation
- Concept2 CSV/Logbook import (ErgData export)
- Strava OAuth2 integration (auto-sync rowing activities)
- Unified data model normalizing all three sources
- User profiles with registration/login (private by default)
- Team system: create team, invite members, shared data
- Visualizations: time-series progress, PBs, volume tracking, team leaderboard
- Dashboard: personal stats, recent activity, streaks

## Tech Stack (Default — confirm before diverging)
- Frontend: React / Next.js (TypeScript) + TailwindCSS
- Backend: Python (FastAPI) or Node.js (Express/NestJS) — confirm with user
- Database: PostgreSQL
- Auth: Supabase Auth, Clerk, or Firebase Auth
- Charts: Recharts or ECharts

## Constraints & Rules
- **MVP scope only** — do NOT build training plans, BLE/real-time sync, social features beyond teams, or export reports unless explicitly requested
- **Mobile-responsive** — athletes check stats on phones
- **Privacy-first** — data sharing is opt-in, default to private
- Write tests for data parsers (Concept2 CSV, Strava API) before wiring them into the UI
- Use environment variables for all API keys and secrets
- Commit messages: conventional commits format (feat:, fix:, chore:, docs:)

## Workflow
- Before writing code, check AGENTS.md, PLAN.md, and any relevant files for context
- When adding a new dependency, justify with a brief comment or commit message
- Run the existing test suite before submitting changes
- If the user hasn't chosen backend language yet, ask before scaffolding

## Files Not to Touch
- .env files (ask user for credentials)
- node_modules/, .venv/, __pycache__/ (gitignored)
