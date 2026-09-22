# MentorPulse 🎓⚡

> **Skill-Based Mentor Matching & Progress Tracking Platform**

MentorPulse connects learners looking to develop specific technical, design, or business skills with qualified mentors. The platform manages the full mentorship lifecycle including discovery, request/acceptance, session tracking, milestone progress, resource sharing, and achievement badges.

---

## 🚀 Features Implemented

### Phase 1: Foundation, Design System & User Accounts
- **Modern Glassmorphic UI**: High-contrast, responsive dark-slate design system with Inter / Plus Jakarta Sans typography, badge tokens, and micro-interactions.
- **Dual-Role User Architecture**: Users can simultaneously hold `Mentor` and `Learner` roles, toggling seamlessly between them.
- **Skills Portfolio**: Normalized skill model across categories (*Programming*, *Design*, *Data Science & AI*, *Business & Product*, *Other*).
- **Profile Management**: Experience level badges, availability settings, personal bios, and structured learning goals.
- **Role-Aware Dashboard**: Dynamic landing page featuring active role badges, skills portfolio, stats widgets, and role perspective workspaces.

### Phase 2: Mentor Discovery & Matching Engine
- **Mentor Directory & Filtering**: Multi-criteria search by skill, category, experience level, and availability.
- **Algorithmic Compatibility Scoring**: Dynamic match scores (0-100%) calculated based on skill overlap, category alignment, experience differential, and availability.
- **Priority Fast-Track Flagging**: Visual indicators and badges for verified mentors and active collaborations.

### Phase 3: Mentorship Lifecycle & Workspaces
- **Mentorship Request Flow**: Complete request lifecycle (Pending -> Accepted -> In Progress -> Completed / Cancelled / Rejected).
- **Collaborative Workspaces**: Unified dashboard with session scheduler, roadmap milestones checklist, resource sharing, and threaded discussions.
- **Progress Tracking**: Real-time progress bar calculation based on completed roadmap milestones.
- **Credential Certificates**: Unlocked upon completing all mentorship milestones with verification hash.

### Phase 4: Gamification, Credits, Badges & Leaderboard
- **Internal Closed-Loop Credit Economy**:
  - Automatically provisions **50 Credits** on user registration via `post_save` signal.
  - **-10 Credits** for booking a mentorship session; **-5 Credits** for priority queue unlock.
  - **100% Refund guarantee** (+10 or +15 Credits) if a mentorship request is rejected or cancelled.
  - **+10 Credits reward** credited to mentors upon completing meeting sessions.
  - Complete double-entry style audit ledger (`CreditTransaction`) tracking all credit movements.
  - User wallet dashboard (`/wallet/`) with balance cards, total earned, total invested, and transaction history.
- **Feedback & Reputation Ratings**:
  - 1-to-5 star rating system with detailed peer reviews.
  - Workspace integration tab preventing duplicate submissions and updating mentor average rating.
- **Badges & Achievement Showcase**:
  - 5 core badges: *First Steps* (1 completed mentorship), *Committed Mentor* (2+ completed mentorships), *Rising Star* (Skill score >= 8.0), *Top Rated* (4.5+ star review), *Helpful Hand* (2+ shared resources).
  - Achievement gallery (`/badges/`) showing unlocked badges in color with earned date and locked ones in greyscale with progress tracking.
- **Platform Leaderboard**:
  - Dynamic weighted ranking formula: `Score = (Skill Score * 10.0) + (Credit Balance * 0.5) + (Badges * 15.0)`.
  - Top 3 podium cards (Gold, Silver, Bronze), search filter, and authenticated user standing highlight (`/leaderboard/`).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 5.x
- **Database**: SQLite
- **Frontend**: Django Templates, Bootstrap 5, Bootstrap Icons, Custom CSS Design System
- **Authentication**: Built-in Django Auth extended with `Profile`, `Credit`, and `RoleAssignment` models

---

## 🏁 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/fornkb/MentorPulse.git
cd MentorPulse
```

### 2. Install dependencies
```bash
pip install django pillow
```

### 3. Apply database migrations
```bash
python manage.py migrate
```

### 4. Seed all demo accounts and scenarios
```bash
python manage.py seed_phase1
python manage.py seed_phase2
python manage.py seed_phase3
python manage.py seed_phase4
```
This populates skills, mentors, active mentorships, wallets, reviews, badges, and leaderboard rankings:
- **`david_frontend`** / `DemoPass123!` (Mentor — Rank #1 on Leaderboard, 70 CR, 4 badges)
- **`maya_design`** / `DemoPass123!` (Mentor — Rank #2 on Leaderboard, 60 CR, 1 badge)
- **`alex_mentor`** / `DemoPass123!` (Mentor — Expert Backend / Python, 85 CR, 4 badges)
- **`sara_learner`** / `DemoPass123!` (Learner — Active mentorship with David Vance, 25 CR)
- **`charlie_dual`** / `DemoPass123!` (Dual-role — Completed mentorship with Alex Rivera, 40 CR)

### 5. Run the development server
```bash
python manage.py runserver
```
- **Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Find Mentors**: [http://127.0.0.1:8000/mentors/](http://127.0.0.1:8000/mentors/)
- **Mentorships**: [http://127.0.0.1:8000/mentorships/](http://127.0.0.1:8000/mentorships/)
- **Leaderboard**: [http://127.0.0.1:8000/leaderboard/](http://127.0.0.1:8000/leaderboard/)
- **Badges**: [http://127.0.0.1:8000/badges/](http://127.0.0.1:8000/badges/)
- **Wallet**: [http://127.0.0.1:8000/wallet/](http://127.0.0.1:8000/wallet/)

---

## 🧪 Running Unit Tests

Execute the automated test suite across all four apps (47 tests):
```bash
python manage.py test accounts matching mentorship gamification
```

---

## 🗺️ Roadmap

- [x] **Phase 1**: Foundation, Design System & User Accounts
- [x] **Phase 2**: Mentor Discovery, Filtering & Rule-Based Matching Engine
- [x] **Phase 3**: Mentorship Requests, Milestones, Sessions & Resources
- [x] **Phase 4**: Gamification, Credits, Badges & Leaderboards
- [ ] **Phase 5**: Polish, Notifications, Demo Seeder & Certificate Generation



