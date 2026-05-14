# Rowing Proj — Implementation Plan

## Overview
Build a full-stack rowing training app that aggregates workout data from manual input, Concept2, and Strava, with private user profiles and team-based data sharing. This is the MVP — scope will be refined as we go.

---

## Phase 1: Foundation & Architecture

### 1.1 Pick Tech Stack
- [ ] Decide backend language (Python/FastAPI or Node.js/Express)
- [ ] Decide auth provider (Supabase Auth, Clerk, Firebase Auth)
- [ ] Decide charting library (Recharts vs ECharts)

### 1.2 Initialize Project
- [ ] Set up monorepo or separate frontend/backend directories
- [ ] Initialize frontend with Next.js + TypeScript + TailwindCSS
- [ ] Initialize backend with chosen framework
- [ ] Configure ESLint, Prettier, pre-commit hooks
- [ ] Set up GitHub repo with CI (lint + test on push)

### 1.3 Database Schema
- [ ] Design and create `users` table
- [ ] Design and create `profiles` table (weight, height, goal split, max HR)
- [ ] Design and create `teams` table
- [ ] Design and create `team_members` table (role: owner/coach/athlete/viewer)
- [ ] Design and create `workouts` table (unified data model)
- [ ] Design and create `workout_splits` table (interval/split data for Concept2)
- [ ] Design and create `strava_connections` table (tokens, expiry)
- [ ] Run initial migration

---

## Phase 2: Authentication & User Profiles

### 2.1 Auth
- [ ] Set up auth provider SDK
- [ ] Implement registration page (email/password or OAuth)
- [ ] Implement login/logout
- [ ] Protected routes and API middleware

### 2.2 Profile
- [ ] Profile creation flow on first login
- [ ] Profile edit page (personal details, preferences)
- [ ] Privacy default: all data private unless shared

---

## Phase 3: Data Ingestion & Normalization

### 3.1 Manual Entry
- [ ] Build workout log form (date, type, duration, distance, split, HR, notes)
- [ ] Client-side validation
- [ ] API endpoint to save workout
- [ ] List/view/edit/delete logged workouts
- [ ] Unit tests for validation

### 3.2 Concept2 Import
- [ ] Parse Concept2 CSV/Logbook export format
- [ ] Build upload UI (drag-and-drop or file picker)
- [ ] Map CSV fields to unified workout model
- [ ] Handle duplicate detection (same workout already imported)
- [ ] API endpoint to import and store
- [ ] Unit tests for CSV parser

### 3.3 Strava Integration
- [ ] Set up Strava API app (client ID, secret, callback URL)
- [ ] Implement OAuth2 flow (authorize, exchange code for tokens)
- [ ] Token refresh logic (Strava tokens expire after 6 hours)
- [ ] Background sync: fetch recent rowing activities
- [ ] Filter for sport_type = "Rowing" (or water sports)
- [ ] Map Strava activity fields to unified workout model
- [ ] API endpoint to trigger manual sync
- [ ] Unit tests for Strava API adapter

### 3.4 Data Normalization Layer
- [ ] Unified `Workout` model with fields from all sources
- [ ] Normalize units (meters, split/500m, watts, strokes/min, HR)
- [ ] Source tagging (manual/concept2/strava) for dedup and UI badges
- [ ] Merge duplicates based on time + duration + source

---

## Phase 4: Team System

### 4.1 Team Management
- [ ] Create team form (name, description, optional invite-only toggle)
- [ ] Generate shareable invite link or code
- [ ] Join team via invite code
- [ ] Leave / remove member from team
- [ ] Role-based permissions (owner/coach/athlete/viewer)

### 4.2 Team Sharing
- [ ] Per-workout visibility toggle (private / team / public)
- [ ] Team dashboard: aggregate stats, recent team activity feed
- [ ] Team leaderboard: ranked by weekly/monthly volume or time

---

## Phase 5: Visualization & Progress

### 5.1 Personal Dashboard
- [ ] Weekly/monthly volume chart (bar chart)
- [ ] Split progression over time (line chart, split/500m trends)
- [ ] Personal bests table (2k, 5k, 10k, 30min, 60min)
- [ ] Consistency streak calendar (git-style contribution graph)
- [ ] HR zones breakdown (pie/donut chart)

### 5.2 Team Dashboard
- [ ] Team volume over time
- [ ] Member ranking table
- [ ] Team records board

---

## Phase 6: MVP Polish & Launch

### 6.1 UX
- [ ] Mobile-responsive layout
- [ ] Loading states (skeletons/spinners)
- [ ] Empty states (no workouts yet, no team yet)
- [ ] Error boundaries and friendly error messages

### 6.2 Testing
- [ ] Unit tests for all data parsers
- [ ] Integration tests for Strava sync and team flows
- [ ] E2E smoke tests for critical paths (login, log workout, import CSV)

### 6.3 Deployment
- [ ] Frontend: Vercel or Netlify
- [ ] Backend: Render / Railway / Fly.io / AWS
- [ ] Database: Supabase / Neon / managed PostgreSQL
- [ ] Custom domain setup (optional)

### 6.4 Documentation
- [ ] API docs (auto-generated via OpenAPI if FastAPI)
- [ ] Environment variable reference
- [ ] Local dev setup guide in README

---

## Future Iterations (Not MVP)
- Real-time erg data bridge (BLE/PM5)
- Goal setting and training plans
- Export reports (PDF, CSV)
- Social features (follow athletes, comment)
- Structured workout/interval builder
- Coach assignment and workout prescription
- Mobile app (React Native or Expo)
