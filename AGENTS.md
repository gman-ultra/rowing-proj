# RowApp Agent Instructions

You are working in the `~/rowapp` repository.

## Critical Memory Bridge

Your architectural memory, API documentation, testing plans, and Kanban board do NOT live in this repository. They live in the Dev Hub Obsidian Vault.

Before modifying architecture, database schemas, or APIs, you MUST read:
1. `~/obsidian-vaults/dev-hub/01 - Projects/RowApp/RowApp.md`
2. `~/obsidian-vaults/dev-hub/02 - Kanban/RowApp Board.md`
3. `~/obsidian-vaults/dev-hub/01 - Projects/RowApp/Wiki/index.md`

Any time you complete a feature or make a design decision, you MUST write the documentation back to the `dev-hub` vault, NOT to local markdown files in this repository.

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

## Hermes / OpenCode / Codex Workflow — Applies With or Without Kanban

This is the default operating loop for RowApp development:

1. **User tells Hermes what they want.** Main Hermes (`gpt-5.5`) receives the request and acts as the user-facing orchestrator/verifier.
2. **Hermes chooses the execution mode.**
   - **Direct mode / no Kanban:** For small, contained changes, Hermes plans the change, delegates the coding portion to OpenCode, optionally asks Codex for senior review on non-trivial diffs, then verifies and reports back in the same conversation.
   - **Kanban mode:** For multi-step, durable, parallel, or review-heavy work, Hermes routes to the Planner profile (`gpt-5.4`) to create Kanban cards and dependencies. The board then dispatches Researcher/Coder/Implementer/Reviewer/Recorder profiles.
3. **OpenCode does routine code execution.** OpenCode is the default builder for writing and fixing application code. Hermes and Planner should not hand-edit application code unless it is a tiny non-code metadata/doc adjustment or an emergency correction.
4. **Codex acts as senior reviewer/debugger/git steward.** Codex is used for complex reviews, high-risk changes, hard bug diagnosis, CI/test failure analysis, architectural sanity checks, and git/PR hygiene. Codex can write files only for explicitly bounded tasks.
5. **Hermes verifies and integrates.** After OpenCode and/or Codex finishes, Hermes checks diffs, runs relevant tests/commands, wires the result into the system/docs, and reports exactly what changed, what was verified, and what remains.

### Model / Role Routing

- Main Hermes (`gpt-5.5`) and Planner (`gpt-5.4`) are for thinking: planning, decomposition, delegation, and Kanban routing.
- Recorder uses `gpt-5.4-mini` for lower-cost thinking and documentation.
- Routine terminal work, coding, implementation verification, and low-risk code review should use OpenCode Zen models through OpenCode, not direct Hermes edits.
- Prefer free OpenCode Zen models first (`big-pickle`, `deepseek-v4-flash-free`, `qwen3.6-plus-free`, `minimax-m2.5-free`, etc.). If free models are rate-limited/maxed/unusable, use `opencode/minimax-m2.7`.
- Use Codex as the **Senior Engineering Agent** for review/debug/git tasks where stronger reasoning is worth the extra cost or risk: auth, database/schema, privacy/team visibility, API contracts, import/sync logic, complex failing tests, and pre-commit/PR review.
- For live OpenCode work in both direct and Kanban modes, target the tmux session's 3rd window (window index `2`). Use `~/scripts/opencode-kanban-pane.sh [session] [model]` to reuse an existing OpenCode pane or start OpenCode in an idle pane, then send concise prompts with `tmux send-keys`.

## OpenCode Policy

- **All normal code generation must be done via OpenCode CLI.** See the OpenCode skill at `~/.hermes/skills/autonomous-ai-agents/opencode/SKILL.md` for the full interaction pattern (one-shot `opencode run`, tmux pane interaction, etc.).
- Before any coding task, load the skill: `skill_view(name='opencode')`.
- If OpenCode is already running in the tmux session's 3rd window, send prompts to that pane via `tmux send-keys` instead of starting a new session.
- After OpenCode changes files, Hermes must verify the result itself: inspect `git diff`, run relevant tests/type checks, update Dev Hub documentation when needed, and summarize results to the user.

## Codex Policy

- Before Codex work, load the skill: `skill_view(name='codex')`.
- On this WSL/Windows setup, invoke the Windows Codex CLI through PowerShell to use the Windows/Desktop App environment and avoid the mixed Windows-npm/WSL-node dependency issue:
  ```bash
  powershell.exe -NoProfile -Command "codex ..."
  # or use the helper wrapper:
  ~/scripts/codex-win.sh ...
  ```
- Prefer Codex in read/review mode for:
  - reviewing OpenCode diffs before final acceptance
  - diagnosing complex bugs or failing tests
  - security/privacy review for auth, JWTs, team visibility, and API contracts
  - database/schema/migration review
  - git status/diff/commit/PR planning
- Do **not** make Codex the default implementation agent. OpenCode remains the normal builder.
- Codex CLI v0.132.0 has a verified sandbox caveat here: `--sandbox workspace-write` may still resolve to an effective read-only profile. Verify the Codex banner/output before assuming writes are allowed.
- If Codex must write files, use an explicitly scoped prompt and only use `--sandbox danger-full-access` when the user/task has clearly accepted that bounded write risk. Hermes must inspect the resulting diff and run relevant checks afterward.

## Constraints & Rules

- **MVP scope only** — do NOT build training plans, BLE/real-time sync, social features beyond teams, or export reports unless explicitly requested
- **iOS-first** — design for mobile form factor (portrait, touch interactions, safe areas)
- **Privacy-first** — data sharing is opt-in, default to private
- Write tests for data parsers (Concept2 CSV, Strava API) before wiring them into the UI
- Use environment variables for all API keys and secrets
- Commit messages: conventional commits format (feat:, fix:, chore:, docs:)

## Project Structure

```text
rowapp/
  backend/          ← FastAPI (Python) — owned
  frontend/         ← Next.js web admin panel — DEPRECATED for main UI, kept for admin use
  mobile/           ← Expo React Native — PRIMARY frontend
```

## Workflow

- Load `skill_view(name='opencode')` before any code generation task
- Load `skill_view(name='codex')` before Codex review/debug/git tasks
- Before writing code, check AGENTS.md, PLAN.md, and wiki for context
- When adding a new dependency, justify with a brief comment or commit message
- Run the existing test suite before submitting changes

## Files Not to Touch

- .env files (ask user for credentials)
- node_modules/, .venv/, __pycache__/ (gitignored)
