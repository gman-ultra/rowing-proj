# Rowing Proj — Agent Instructions

## Project Identity
We are building an **iOS rowing training app** (with Android support) that aggregates workout data from manual entry, Concept2, and Strava, then visualizes progress. Users have private profiles and can join teams that share data.

**Pivot decision (May 2026):** Frontend is now Expo React Native (iOS-first), not Next.js web. Backend remains Python FastAPI.

## Core Goals (MVP)
- iOS app via Expo React Native (develop on WSL, test via Expo Go on iPhone)
- Manual workout logging form with validation
- Concept2 CSV/Logbook import (ErgData export)
- Strava OAuth2 integration (auto-sync rowing activities)
- Unified data model normalizing all three sources
- User profiles with registration/login via invite code (private by default)
- Team system: create team, invite members, shared data
- Visualizations: time-series progress, PBs, volume tracking, team leaderboard
- Dashboard: personal stats, recent activity, streaks
- App Store release via EAS Build (no Mac needed)

## Tech Stack (Default — confirm before diverging)
- **Mobile:** Expo (React Native) + TypeScript
- **Backend:** Python FastAPI (stays the same)
- **Database:** PostgreSQL via Neon (free tier)
- **Auth:** Custom JWT + invite code (no external provider)
- **Charts:** react-native-chart-kit or victory-native (TBD)
- **Navigation:** react-navigation (stack + tab)

## OpenCode Policy
- **All code generation must be done via OpenCode CLI.** See the OpenCode skill at `~/.hermes/skills/autonomous-ai-agents/opencode/SKILL.md` for the full interaction pattern (one-shot `opencode run`, tmux pane interaction, etc.).
- Before any coding task, load the skill: `skill_view(name='opencode')`
- If the user already has OpenCode running in a tmux pane, send prompts to that pane via `tmux send-keys` instead of starting a new session.

## Constraints & Rules
- **MVP scope only** — do NOT build training plans, BLE/real-time sync, social features beyond teams, or export reports unless explicitly requested
- **iOS-first** — design for mobile form factor (portrait, touch interactions, safe areas)
- **Privacy-first** — data sharing is opt-in, default to private
- Write tests for data parsers (Concept2 CSV, Strava API) before wiring them into the UI
- Use environment variables for all API keys and secrets
- Commit messages: conventional commits format (feat:, fix:, chore:, docs:)

## Project Structure
```
rowapp/
  backend/          ← FastAPI (Python) — owned
  frontend/         ← Next.js web admin panel — DEPRECATED for main UI, kept for admin use
  mobile/           ← Expo React Native — PRIMARY frontend
```

## Workflow
- Load `skill_view(name='opencode')` before any code generation task
- Before writing code, check AGENTS.md, PLAN.md, and wiki for context
- When adding a new dependency, justify with a brief comment or commit message
- Run the existing test suite before submitting changes
- If the user hasn't chosen backend language yet, ask before scaffolding

## Files Not to Touch
- .env files (ask user for credentials)
- node_modules/, .venv/, __pycache__/ (gitignored)
