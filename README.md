# MentorPulse 🎓⚡

> **Skill-Based Mentor Matching & Progress Tracking Platform**

MentorPulse connects learners looking to develop specific technical, design, or business skills with qualified mentors. The platform manages the full mentorship lifecycle including discovery, request/acceptance, session tracking, milestone progress, resource sharing, and achievement badges.

---

## 🚀 Features (Phase 1 Implemented)

- **Modern Glassmorphic UI**: High-contrast, responsive dark-slate design system with Inter / Plus Jakarta Sans typography, badge tokens, and micro-interactions.
- **Dual-Role User Architecture**: Users can simultaneously hold `Mentor` and `Learner` roles, toggling seamlessly between them.
- **Skills Portfolio**: Normalized skill model across categories (*Programming*, *Design*, *Data Science & AI*, *Business & Product*, *Other*).
- **Profile Management**: Experience level badges, availability settings, personal bios, and structured learning goals.
- **Role-Aware Dashboard**: Dynamic landing page featuring active role badges, skills portfolio, stats widgets, and role perspective workspaces.
- **Django Admin Integration**: Full administrative control over users, profiles, skills, and role assignments.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Django 5.x
- **Database**: SQLite
- **Frontend**: Django Templates, Bootstrap 5, Bootstrap Icons, Custom CSS Design System
- **Authentication**: Built-in Django Auth extended with `Profile` and `RoleAssignment` models

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

### 4. Seed initial skills & demo accounts
```bash
python manage.py seed_phase1
```bash
python manage.py seed_phase1
python manage.py seed_phase2
python manage.py seed_phase3
```
This populates 27 categorized skills, diverse mentor profiles, and real-world mentorship lifecycle scenarios:
- **`david_frontend`** / `DemoPass123!` (Mentor — Advanced Frontend / React)
- **`maya_design`** / `DemoPass123!` (Mentor — Expert Product Design / Figma)
- **`priya_ai`** / `DemoPass123!` (Mentor — Expert AI & Deep Learning)
- **`marcus_cloud`** / `DemoPass123!` (Mentor — Advanced DevOps / Cloud)
- **`sarah_product`** / `DemoPass123!` (Mentor — Advanced Product & Career Coaching)
- **`alex_mentor`** / `DemoPass123!` (Mentor — Expert Backend / Python)
- **`sara_learner`** / `DemoPass123!` (Learner — Active mentorship with David Vance, pending priority request to Maya Lin)
- **`charlie_dual`** / `DemoPass123!` (Dual-role — Completed mentorship with Alex Rivera, unlocked certificate)

### 5. Run the development server
```bash
python manage.py runserver
```
Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/), explore mentors at [http://127.0.0.1:8000/mentors/](http://127.0.0.1:8000/mentors/), or view collaborative workspaces at [http://127.0.0.1:8000/mentorships/](http://127.0.0.1:8000/mentorships/).

---

## 🧪 Running Unit Tests

Execute the automated test suite with:
```bash
python manage.py test mentorship matching accounts
```

---

## 🗺️ Roadmap

- [x] **Phase 1**: Foundation, Design System & User Accounts
- [x] **Phase 2**: Mentor Discovery, Filtering & Rule-Based Matching Engine
- [x] **Phase 3**: Mentorship Requests, Milestones, Sessions & Resources
- [ ] **Phase 4**: Gamification, Credits, Badges & Leaderboards
- [ ] **Phase 5**: Polish, Notifications, Demo Seeder & Certificate Generation


