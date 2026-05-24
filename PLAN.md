# Rowing Proj — Implementation Plan

> **🧑‍💻 AI Agents:** Hermes orchestrates/verifies, OpenCode is the default builder for normal code generation, and Codex is the senior reviewer/debugger/git steward for complex or high-risk work. Load `skill_view(name='opencode')` before coding and `skill_view(name='codex')` before Codex review/debug/git tasks. See `AGENTS.md` for routing rules and WSL/Windows Codex bridge details.

## Overview
Build an iOS (and Android) rowing training app that aggregates workout data from manual input, Concept2, and Strava, with private user profiles and team-based data sharing. This is the MVP — scope will be refined as we go.

**Key decision (May 2026):** Frontend pivot from Next.js web app → Expo React Native (iOS-first). The Next.js frontend directory (`frontend/`) is retained as a lightweight admin panel but all user-facing development happens in `mobile/` (Expo).

---

## Phase 0: iOS/Expo Foundation

### 0.1 Apple Developer Setup
- [ ] Register Apple Developer account ($99/yr)
- [ ] Set up App Store Connect team
- [ ] Create app bundle identifier

### 0.2 Initialize Expo Project
- [ ] Create `/home/gbunkers/rowapp/mobile/` with `npx create-expo-app`
- [ ] Configure `app.json` (app name, icon, bundle ID, scheme)
- [ ] Install shared dependencies (react-navigation, axios, expo-secure-store)
- [ ] Set up TypeScript config
- [ ] Verify Expo Go works on iPhone (QR scan from WSL)

### 0.3 Backend Connection
- [ ] Set up API client (axios base URL for dev → local network IP)
- [ ] Store JWT tokens in expo-secure-store
- [ ] Create shared API types (mirror Pydantic schemas)

---

## Phase 1: Foundation & Architecture

### 1.1 Tech Stack (Decided)
- [x] Backend: Python FastAPI ✅
- [x] Auth: Custom JWT + invite code (no external provider) ✅
- [ ] Mobile: Expo React Native (iOS-first)
- [ ] Charting: react-native-chart-kit or victory-native (TBD)
- [x] Database: PostgreSQL (via Neon free tier) ✅

### 1.2 Initialize Backend Project
- [x] Monorepo structure ✅
- [x] FastAPI scaffold (routers, models, schemas, services) ✅
- [x] SQLAlchemy models (user, workout, team, etc.) ✅
- [x] ESLint, Prettier (TBD)
- [ ] Set up GitHub repo with CI (lint + test on push)

### 1.3 Database Schema
- [x] Users table ✅
- [ ] Profiles table (weight, height, goal split, max HR) — stretch
- [x] Teams table ✅
- [x] Team members table (role: owner/coach/athlete/viewer) ✅
- [x] Workouts table (unified data model) ✅
- [x] Workout splits table (interval/split data for Concept2) ✅
- [x] Strava connections table (tokens, expiry) ✅
- [ ] Run initial migration (SQLite for dev, Neon for prod)

---

## Phase 2: Authentication & User Profiles

### 2.1 Auth (Backend — Done)
- [x] Custom JWT register/login/me endpoints ✅
- [x] bcrypt password hashing ✅
- [x] Invite code validation + auto-teammember creation ✅
- [x] Seed script: default "Rowing Club" team ✅

### 2.2 Auth (Mobile — Build)
- [ ] Login screen (email + password)
- [ ] Register screen (email + password + display name + invite code)
- [ ] Secure JWT storage (expo-secure-store)
- [ ] Auth context / protected routes
- [ ] Logout

### 2.3 Profile
- [ ] Profile view screen
- [ ] Profile edit (personal details)
- [ ] Privacy default: all data private unless shared

---

## Phase 3: Data Ingestion & Normalization

### 3.1 Manual Entry (Mobile)
- [ ] Workout log form (date, type, duration, distance, split, HR, notes)
- [ ] Client-side validation
- [ ] API endpoint to save workout ✅ (stub exists)
- [ ] List/view/edit/delete logged workouts
- [ ] Pull-to-refresh, loading states

### 3.2 Concept2 Import
- [ ] Parse Concept2 CSV/Logbook export format
- [ ] File picker (expo-document-picker)
- [ ] Map CSV fields to unified workout model
- [ ] Handle duplicate detection
- [ ] API endpoint to import and store
- [ ] Unit tests for CSV parser

### 3.3 Strava Integration
- [ ] Set up Strava API app (client ID, secret, callback URL)
- [ ] Implement OAuth2 flow (deep link back to app after authorize)
- [ ] Token refresh logic (Strava tokens expire after 6 hours)
- [ ] Background sync: fetch recent rowing activities
- [ ] Filter for sport_type = "Rowing"
- [ ] Map Strava activity fields to unified workout model
- [ ] API endpoint to trigger manual sync
- [ ] Unit tests for Strava API adapter

### 3.4 Data Normalization Layer
- [ ] Unified `Workout` model with fields from all sources
- [ ] Normalize units (meters, split/500m, watts, strokes/min, HR)
- [ ] Source tagging for dedup and UI badges
- [ ] Merge duplicates based on time + duration + source

---

## Phase 4: Team System (Mobile)

### 4.1 Team Management
- [ ] Create team screen (name, description)
- [ ] Display invite code (QR or text)
- [ ] Join team via invite code input
- [ ] Leave / remove member
- [ ] Role-based permissions (owner/coach/athlete/viewer)

### 4.2 Team Sharing
- [ ] Per-workout visibility toggle (private / team / public)
- [ ] Team dashboard: aggregate stats, recent team activity feed
- [ ] Team leaderboard: ranked by weekly/monthly volume or time

---

## Phase 5: Visualization & Progress (Mobile)

### 5.1 Personal Dashboard
- [ ] Weekly/monthly volume chart (bar)
- [ ] Split progression over time (line chart)
- [ ] Personal bests table (2k, 5k, 10k, 30min, 60min)
- [ ] Consistency streak calendar
- [ ] HR zones breakdown

### 5.2 Team Dashboard
- [ ] Team volume over time
- [ ] Member ranking table
- [ ] Team records board

---

## Phase 6: MVP Polish & Launch

### 6.1 UX
- [ ] Native feel: swipe navigation, haptics, gestures
- [ ] Loading states (skeletons/spinners)
- [ ] Empty states (no workouts yet, no team yet)
- [ ] Error boundaries and friendly error messages
- [ ] Dark mode

### 6.2 Testing
- [ ] Unit tests for all data parsers
- [ ] Integration tests for Strava sync and team flows
- [ ] E2E smoke tests for critical paths

### 6.3 Deployment
- [ ] Set up EAS Build (Expo cloud build for iOS)
- [ ] Configure TestFlight internal testing
- [ ] Backend: Render / Railway / Fly.io
- [ ] Database: Neon (PostgreSQL free tier)
- [ ] Custom domain (optional)
- [ ] Submit to App Store

### 6.4 Documentation
- [ ] API docs (auto-generated via FastAPI OpenAPI)
- [ ] Environment variable reference
- [ ] Local dev setup guide in README

---

## Future Iterations (Post-MVP)
- Real-time erg data bridge (BLE/PM5)
- Goal setting and training plans
- Export reports (PDF, CSV)
- Social features (follow athletes, comment)
- Structured workout/interval builder
- Coach assignment and workout prescription
- Android release (Expo handles this easily once iOS is done)
- Push notifications
- Apple Watch app
