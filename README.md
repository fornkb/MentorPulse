# MentorPulse 🎓⚡

> **Skill-Based Mentor Matching & Progress Tracking Platform**
> **Version 1.0 (Phase 1–5 Complete — Production-Ready Demo)**

MentorPulse connects learners looking to develop specific technical, design, or business skills with qualified mentors. The platform manages the full mentorship lifecycle: algorithmic discovery, priority booking, live session tracking, discrete milestone progress, resource sharing, in-app notifications, achievement badges, and print-ready credential certificates.

---

## ⚡ 1-Click Launch (Windows)

To start the app immediately on Windows with automatic migration, turnkey demo data seeding, and auto-opening the browser:

```bat
# Double-click or run from command prompt:
debug.bat
```
*(Or simply run `run_demo.bat`)*

This script:
1. Verifies Python availability.
2. Applies database migrations automatically.
3. Runs `python manage.py seed_demo_data` to ensure all demo accounts, mentorships, and notifications are ready.
4. Opens your default web browser to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).
5. Launches the local development server.

---

## 🚀 Key Features (Phase 1 to Phase 5)

### 1. In-App Notification Center (`notifications` app)
- **Centralized Event Dispatching**: Real-time notifications dispatched for incoming mentorship requests, approvals, declinations, session reminders, mutual reviews, and unlocked badges.
- **Top Navbar Bell Menu**: Dynamic dropdown with unread badge counter and fast previews of the 5 most recent notifications.
- **Full Notification Hub (`/notifications/`)**: Tabbed inbox filtering (*All* vs *Unread*), "Mark all as read", "Clear read", and 1-click routing directly to relevant workspaces or certificates.

### 2. One-Click Demo Role & User Switcher
- **Instant Swap**: Located in the top navbar (`⚡ Demo Switcher`). Allows evaluators and reviewers to swap between any demo account in under 1 second without logging out or re-entering passwords.
- Categorized into:
  - **Administrator / Superuser**: `admin`
  - **Mentors**: Sarah Connor (Python), Marcus Vance (React), Dr. Elena Rostova (AI/Data), Alex Morgan (UI/UX), David Kim (DevOps)
  - **Learners**: Alex Rivera (Python/Django), Priya Sharma (React/Frontend), Jordan Lee (Data Science)

### 3. Turnkey Demo Data Seeder (`seed_demo_data`)
- Run with a single command: `python manage.py seed_demo_data`.
- Cleans and regenerates:
  - **Skills Taxonomy**: 25+ standardized skills across Programming, Design, Data, Business, and DevOps.
  - **Starter Badges**: First Steps, Committed Mentor, Rising Star, Top Rated, Helpful Hand.
  - **Active Mentorship**: Sarah Connor & Alex Rivera (67% progress, past & upcoming sessions, Google Meet links, resources, discussion posts).
  - **Completed Mentorship**: Marcus Vance & Priya Sharma (100% complete roadmap, 5-star mutual ratings, unlocked credential certificate).
  - **Pending Priority Request**: Jordan Lee $\rightarrow$ Sarah Connor (-15 credits deducted, ⭐ Priority tag in Sarah's inbox).
  - Pre-computed leaderboard scores and populated notification inboxes.

### 4. Mentorship Lifecycle & Collaborative Workspaces
- **Rule-Based Matching Engine**: Evaluates skill overlap, schedule compatibility, and experience gaps to score compatibility (0–100%).
- **Interactive Workspaces**: Shared dashboard with meeting scheduler, copy-to-clipboard meeting link buttons with toast feedback, interactive milestones checklist, resource uploader (docs, links, notes), and async discussions.
- **Completion Credential Certificate**: Printable, styled completion certificate accessible once a mentorship is marked completed.

### 5. Gamification, Credit Economy & Leaderboard
- **50 Starting Credits** automatically provisioned on registration.
- **Transparent Wallet Ledger**: Auditable log of request deductions (-10 / -15 for priority), session completions (+10 to mentor), and refunds.
- **Real-Time Leaderboard**: Dynamically ranked podium based on `(Skill Score * 10) + (Credits * 0.5) + (Badges * 15)`.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, Django 5.x
- **Database**: SQLite (Zero configuration, file-based, local-only)
- **Frontend**: Django Templates, Bootstrap 5, Bootstrap Icons, Custom CSS Design System
- **Authentication**: Django built-in auth with `Profile`, `Credit`, and `RoleAssignment` models

---

## 🏁 Cross-System Setup Guide (Clean Installation)

Follow these steps to run MentorPulse on any other system (Windows, macOS, or Linux):

### 1. Clone the repository
```bash
git clone https://github.com/fornkb/MentorPulse.git
cd MentorPulse
```

### 2. (Optional but recommended) Create a virtual environment
```bash
# On Windows:
python -m venv venv
venv\Scripts\activate

# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Install requirements
```bash
pip install -r requirements.txt
```

### 4. Run database migrations
```bash
python manage.py migrate
```

### 5. Seed turnkey demonstration data
```bash
python manage.py seed_demo_data
```

### 6. Start the development server
```bash
python manage.py runserver
```

Open your browser at **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**.

---

## 👥 Demo Accounts Directory

All demo accounts share the password: **`DemoPass123!`**

| Username | Role | Specialization / Scenario |
|---|---|---|
| **`admin`** | Superuser / Admin | Full staff access, system administration |
| **`sarah_backend`** | Mentor | Senior Backend Architect (Python, Django, PostgreSQL, Docker) |
| **`marcus_frontend`** | Mentor | Lead Frontend Engineer (React, TypeScript, UI/UX Design) |
| **`dr_elena`** | Mentor | AI Researcher & Data Scientist (PhD Applied Math) |
| **`alex_design`** | Mentor | Staff Product Designer (Figma, Design Systems) |
| **`david_devops`** | Mentor | SRE & Cloud Architect (Docker, CI/CD) |
| **`alex_learner`** | Learner | Active Mentorship with Sarah Connor (67% progress) |
| **`priya_learner`** | Learner | Completed Mentorship with Marcus Vance & Unlocked Certificate |
| **`jordan_learner`** | Learner | Sent Priority Mentorship Request to Sarah Connor (-15 Credits) |

> 💡 **Tip**: When running locally (`DEBUG=True`), you don't even need to type credentials! Simply click **⚡ Demo Switcher** in the top navigation bar to switch between any of these users instantly.

---

## 🧪 Running Automated Tests

Run the complete test suite across all 5 domain apps:

```bash
python manage.py test
```

Expect **53 tests** passing with code 0 (`OK`).

---

## 📄 License & Origin

Developed as part of the MentorPulse skill-based platform project. Built locally with 100% open-source tools.
