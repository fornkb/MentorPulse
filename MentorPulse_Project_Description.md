# MentorPulse — Project Description & Implementation Specification

**Version:** 1.1 (Updated for Feasible Implementation) — for handoff to implementation
**Origin:** Adapted from Group 11 (NPCs) UML design set (activity, class, component, deployment, flowchart, ER, object, sequence, collaboration, and use case diagrams) — rescoped for a buildable, local-only college project.

---

## 1. Project Overview

MentorPulse is a skill-based mentor-matching web platform. Learners looking to develop a skill are matched with mentors who can teach it. The platform manages the full lifecycle of a mentorship: discovery, request/acceptance, session tracking, resource sharing, feedback, and completion — with an internal, non-monetary **credit economy**, **badges**, and a **leaderboard** layered on top to keep both sides engaged.

This is a **local-only, single-team, no-hosting** build. There is no real payment processing, no cloud infrastructure, and no third-party video integration. Anywhere the original design called for an external/paid service, it has been replaced with a simple internal equivalent (see Section 4).

---

## 2. Actors / Roles

| Actor | Description |
|---|---|
| **Learner** | A user seeking mentorship in a skill. Can browse/request mentors, attend sessions, track progress, give feedback, spend credits. |
| **Mentor** | A user offering mentorship. Can set availability, accept/reject requests, log sessions, share resources, earn credits. |
| **Dual-role user** | Any user can hold both a Mentor and a Learner role assignment simultaneously (per the original `RoleAssignment` design — a user is not locked to one role). |
| **System Administrator** | Staff-level user. Moderates resources/discussion threads, manages badge definitions, can adjust credit balances for support/testing. Implemented via Django's built-in staff/superuser permissions + Django Admin — no separate admin UI needs to be built. |

---

## 3. Final Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| Backend framework | **Django (Python 3.11+, Django 5.x)** | Chosen over Node/Express for built-in auth, ORM, migrations, and the free Django Admin panel (huge time saver for a data-model-heavy project like this). |
| Database | **SQLite** (Django default) | File-based, zero setup, sufficient for a college-scale demo. No separate DB server. |
| Auth | **Django's built-in auth system** (`django.contrib.auth`), extended with a `Profile` model (OneToOne to `User`) | No JWT, no OAuth required. Email/username and password is sufficient. |
| Frontend | **Django templates + Modern CSS & Bootstrap 5 (via CDN)** | Server-rendered for speed and simplicity. Enhanced with modern design elements (Inter font, clean card surfaces, status pills, responsive layout) to look polished and production-ready without an npm build step. |
| Admin/testing tooling | **Django Admin** (`/admin/`) | Used to create test users, mentors, mentorships, badges, and to fill data during development/demo without building custom CRUD screens. |
| File storage | Local filesystem via Django's `MEDIA_ROOT`/`MEDIA_URL` | Restricted to common document/image formats (PDF, PNG, JPG, TXT, DOCX) up to 10MB per upload. |
| Background jobs | **None** — all logic (credit updates, badge checks, leaderboard recalculation) runs synchronously inside the relevant view/model save logic | No Celery, no message queue. Fine at this scale. |
| Caching | **None** | No Redis. Not needed at demo scale. |
| Video calls | **External link only** (Google Meet / Zoom URL pasted as plain text into the session record) | No API integration. |
| Payments | **None, ever** | "MentorPulse Credits" are an internal, closed-loop point system with no real-world monetary value or conversion. |
| Notifications | **In-app only** (bell icon / notifications list with unread counter, generated on relevant events) | No email/SMS integration. Kept local and reliable. |
| Hosting/Deployment | **None** | Runs entirely on a local machine via `python manage.py runserver`. No deployment step, no environment variables for cloud services, no domain needed. Demo is shown from localhost or a screen-share. |

---

## 4. Scope Decisions — What Changed from the Original Design and Why

| Original design element | Final decision | Rationale |
|---|---|---|
| AI/ML matching API | Rule-based scoring function in Python (skill overlap + availability overlap + experience level) | No ML infrastructure needed; produces the same ranked-list behavior for a demo. |
| Payment gateway (Stripe) | Removed entirely | Credits are internal-only; no money ever changes hands. |
| Video session API (Zoom/Daily.co) | Plain text meeting link field | Integration adds no functional value for a demo. |
| Redis, message queue, S3, CDN | Removed | Unnecessary at this scale; one SQLite DB + local media folder is sufficient. |
| Microservices (6 separate services) | Single Django project consolidated into 5 domain apps (`accounts`, `mentorship`, `matching`, `gamification`, `notifications`) | Prevents circular import issues and migration dependency headaches while strictly maintaining domain separation. |
| Comma-separated skills string | Normalized `Skill` model with `ManyToManyField` on `Profile` | Avoids case/whitespace mismatch bugs during matching scoring and enables clean filter tags. |
| JSON-based milestone tracking | Discrete relational `Milestone` model under `Mentorship` | Simplifies template forms, checkbox toggling, and completion percentage calculation. |
| Abstract priority queue | Visual priority tag (`is_priority=True`) on mentorship requests | Tangibly reflects the -5 credit deduction with a visible "Priority" badge in the mentor inbox. |
| Mobile app + offline cache | Removed | Responsive web covers this. |
| OAuth / SSO | Not included in v1 | Email/username & password via Django auth is sufficient. |
| Email/SMS notifications | In-app notifications only | Keeps scope buildable; core UX doesn't depend on external SMTP. |
| Calendar API sync | Removed | Manual date/time entry on session records. |
| Hosting/deployment | Removed | Runs and is demoed locally only. |

---

## 5. Feature Set

### 5.1 Core Features (must-have)

1. **Authentication & Profile** — register, login, logout; edit profile (skills, goals, experience level, availability).
2. **Role Assignment** — a user can be a Mentor, a Learner, or both, each with its own role record.
3. **Mentor Discovery & Matching** — learner searches/filters mentors; results ranked by a scoring function (skill overlap, availability, experience).
4. **Mentorship Request Flow** — learner sends a request → mentor accepts (creates a `Mentorship` record with goals/milestones) or rejects (learner notified, credits refunded).
5. **Session Logging** — manually log sessions against a mentorship: date, notes, external meeting link, mark complete.
6. **Progress Tracking** — completion percentage, milestone checklist, skill score, updated as sessions and milestones complete.
7. **Feedback & Ratings** — both mentor and learner can rate (1–5 stars) and comment on each other after sessions or on mentorship completion.
8. **Credit System** — internal points; learners spend, mentors earn (see Section 9.1).
9. **Badges** — rule-based achievements, auto-awarded on event triggers (see Section 9.2).
10. **Leaderboard** — real-time ranked view by score, recalculated on relevant events (see Section 9.3).

### 5.2 Added Features (Feasibility & Demo Polish)

11. **Learning Resource Sharing** — a mentor (or learner) can attach a resource (file upload up to 10MB, link, or note) to a specific mentorship.
12. **Discussion Thread per Mentorship** — simple async comment thread on each mentorship for questions/answers between sessions.
13. **Credits with Priority Unlock** — credits are spent on requests (-10) and optional priority queue placement (-5) with a visual priority badge in the mentor inbox.
14. **In-App Notifications** — created on key events (request received, request accepted/rejected, feedback received, badge earned) with unread badge count.
15. **One-Click Demo Role/User Switcher** — quick switcher in the top navigation bar during development/demo to effortlessly swap between test mentors and learners without relogging.
16. **Automated Demo Seeder** — management command (`python manage.py seed_demo_data`) that populates mentors, learners, skills, active mentorships, milestones, badges, and leaderboard entries for an instant, rich live demo.

### 5.3 Stretch Goals (nice-to-have, not required for demo)

- **Print-Friendly Completion Certificate** — clean, print-styled HTML certificate view (`/mentorship/<id>/certificate/`) accessible when a mentorship is marked completed, rendering a printable credential without heavy external PDF libraries.
- Google/Apple OAuth login.
- Email notifications alongside in-app ones.

### 5.4 Explicitly Out of Scope (do not build)

- Real-time chat / websockets
- Calendar sync / automated scheduling
- Real video call integration
- Payment processing of any kind
- File versioning or rich embedded media (quizzes, video players) inside resources
- Redis, S3, message queues, CDN, microservices
- Mobile app / offline mode
- Cloud hosting or deployment of any kind

---

## 6. Suggested Django Project Structure

To avoid migration tangles and circular imports, models are organized into **5 clean domain apps**:

```
mentorpulse/
├── manage.py
├── mentorpulse/               # project settings, root urls.py, base configuration
├── accounts/                  # User, Profile, RoleAssignment, Skill, auth views
├── matching/                  # Mentor directory, filter views, scoring engine
├── mentorship/                # Mentorship, Session, Progress, Milestone, Resource, DiscussionPost
├── gamification/              # Credit, CreditTransaction, Feedback, Badge, UserBadge, Leaderboard, LeaderboardEntry
├── notifications/             # Notification model, bell dropdown, feed views
├── templates/                 # Shared base templates, navbar, footer, modals
├── static/                    # Custom CSS, JS helpers, UI assets
└── media/                     # Uploaded resource files (PDF, images, docs <= 10MB)
```

This preserves 100% of the original UML component capabilities while fitting naturally into Django’s architecture.

---

## 7. Data Model

Field types are given in Django-style shorthand. FK = ForeignKey, O2O = OneToOneField, M2M = ManyToManyField.

### `accounts` app

**Skill**
- `name` — CharField(unique=True, max_length=100)
- `category` — CharField(max_length=100, choices: `Programming / Design / Data / Business / Other`)

**Profile** (O2O → Django `User`)
- `skills` — M2M → Skill
- `goals` — TextField(blank=True)
- `experience_level` — CharField, choices: `Beginner / Intermediate / Advanced / Expert`
- `availability` — CharField, choices/text (e.g. `Weekdays / Weekends / Flexible`)
- `skill_score` — FloatField, default 0
- `bio` — TextField(blank=True)

**RoleAssignment**
- `user` — FK → User
- `role` — CharField, choices: `Mentor / Learner`
- `start_time` — DateTimeField (auto on creation)
- `end_time` — DateTimeField, nullable
- `context` — TextField, optional notes

---

### `mentorship` app

**Mentorship**
- `mentor` — FK → User (related_name="mentor_mentorships")
- `learner` — FK → User (related_name="learner_mentorships")
- `start_date` — DateField(auto_now_add=True)
- `end_date` — DateField, nullable (set on completion)
- `status` — CharField, choices: `PENDING / ACTIVE / COMPLETED / REJECTED / CANCELLED`, default `PENDING`
- `goals` — TextField (set on request / acceptance)
- `is_priority` — BooleanField, default False (set if learner unlocks priority)

**Session**
- `mentorship` — FK → Mentorship
- `date` — DateTimeField
- `meeting_link` — URLField, optional (Google Meet/Zoom link)
- `notes` — TextField, optional
- `is_completed` — BooleanField, default False

**Milestone**
- `mentorship` — FK → Mentorship (related_name="milestones")
- `title` — CharField(max_length=255)
- `is_completed` — BooleanField, default False
- `completed_at` — DateTimeField, nullable

**Progress**
- `mentorship` — O2O → Mentorship
- `completion_pct` — FloatField, default 0 (computed from completed milestones & sessions)
- `skill_score` — FloatField, default 0
- `tasks` — TextField(blank=True)

**Resource**
- `mentorship` — FK → Mentorship
- `uploaded_by` — FK → User
- `title` — CharField(max_length=200)
- `type` — CharField, choices: `LINK / FILE / NOTE`
- `content` — TextField(blank=True) (URL for link, text for note)
- `file` — FileField(upload_to="resources/", blank=True, null=True) (restricted to docs/images <= 10MB)
- `created_at` — DateTimeField, auto

**DiscussionPost**
- `mentorship` — FK → Mentorship
- `author` — FK → User
- `text` — TextField
- `created_at` — DateTimeField, auto

---

### `gamification` app

**Credit**
- `user` — O2O → User
- `balance` — IntegerField, default = 50 (starting balance)
- `updated_at` — DateTimeField, auto

**CreditTransaction**
- `user` — FK → User
- `amount` — IntegerField (positive = earned, negative = spent)
- `reason` — CharField, choices: `STARTING_BONUS / SESSION_REQUEST / SESSION_REFUND / SESSION_COMPLETED_REWARD / PRIORITY_UNLOCK / ADMIN_ADJUSTMENT`
- `created_at` — DateTimeField, auto

**Feedback**
- `mentorship` — FK → Mentorship
- `given_by` — FK → User
- `given_to` — FK → User
- `rating` — IntegerField (1–5)
- `comments` — TextField, optional
- `created_at` — DateTimeField, auto

**Badge**
- `name` — CharField(unique=True)
- `description` — TextField
- `icon` — CharField(max_length=50, default="award") # Icon identifier

**UserBadge**
- `user` — FK → User
- `badge` — FK → Badge
- `earned_date` — DateTimeField, auto

**Leaderboard**
- `type` — CharField, default="OVERALL"
- `period_start` — DateField, nullable
- `period_end` — DateField, nullable

**LeaderboardEntry**
- `leaderboard` — FK → Leaderboard
- `user` — FK → User
- `score` — FloatField
- `rank` — IntegerField

---

### `notifications` app

**Notification**
- `user` — FK → User
- `message` — CharField(max_length=255)
- `type` — CharField, choices: `REQUEST_RECEIVED / REQUEST_ACCEPTED / REQUEST_REJECTED / SESSION_LOGGED / FEEDBACK_RECEIVED / BADGE_EARNED`
- `is_read` — BooleanField, default False
- `link` — CharField(max_length=255, blank=True) # URL to relevant page
- `created_at` — DateTimeField, auto

---

## 8. Core User Flows

**Flow 1 — Registration & Profile Setup**
User registers → redirected to complete `Profile` (skills, goals, experience, availability) → activates `RoleAssignment` (Mentor and/or Learner).

**Flow 2 — Mentor Discovery & Matching**
Learner opens mentor directory → filters by skill, availability, experience level → `matching` engine calculates fit score (skill overlap, availability, experience) → displays ranked list with match percentages.

**Flow 3 — Request & Acceptance Flow**
Learner sends request (optionally checks "Priority Request" for 5 additional credits) → system verifies credit balance (10 credits for standard, 15 for priority) → credits deducted, `Mentorship` created as `PENDING` → mentor receives notification → mentor accepts (`ACTIVE`, notifications sent) or rejects (`REJECTED`, credits refunded to learner).

**Flow 4 — Sessions & Progress Tracking**
Under active mentorship, mentor or learner logs a `Session` (date, meeting link, notes) → session marked complete → `Milestone` items checked off → `Progress.completion_pct` recalculated → mentor receives +10 credits → badge check triggers → leaderboard recalculated.

**Flow 5 — Resource Sharing & Discussions**
Either party uploads a resource (file/link/note) or posts in the mentorship discussion thread → both visible in the shared mentorship workspace.

**Flow 6 — Feedback & Completion**
After sessions or when all milestones are done, either party submits 1–5 star `Feedback` with comments → mentor marks mentorship `COMPLETED` → print-friendly Certificate becomes accessible.

---

## 9. Business Rules

### 9.1 Credit System

| Event | Effect |
|---|---|
| New user account created | Starting balance: **+50 credits** |
| Learner sends a mentorship request | **−10 credits** (deducted on send; refunded if mentor rejects) |
| Mentor completes a session | **+10 credits** to mentor |
| Learner unlocks priority placement | **−5 credits** (marks request as Priority with visual highlight) |
| Insufficient balance | Block action; display prompt to earn credits by mentoring others |
| Admin manual adjustment | Any amount, staff-only, logged with `ADMIN_ADJUSTMENT` |

Every balance change creates an auditable `CreditTransaction` record.

### 9.2 Badge Rules (Starter Set)

| Badge | Trigger Condition |
|---|---|
| **First Steps** | User completes their first mentorship (as mentor or learner) |
| **Committed Mentor** | Mentor completes 5 mentorships |
| **Rising Star** | User's `skill_score` exceeds 80 |
| **Top Rated** | Average feedback rating ≥ 4.5 across at least 5 ratings received |
| **Helpful Hand** | User shares 5+ resources across all their mentorships |

Badge checks execute synchronously upon event completion.

### 9.3 Leaderboard Rules

- Computed real-time on: session completion, mentorship completion, feedback submission, badge award.
- Global `OVERALL` leaderboard calculates score:
  `score = skill_score + (credit_balance × 0.5) + (badge_count × 10)`
- Ranks are dynamically updated and rendered with top performer badges.

---

## 10. System Administrator Capabilities

Managed via standard Django Admin (`/admin/`):
- View and manage Users, Profiles, Mentorships, Sessions, Feedback
- Create and edit Badge definitions
- Manually adjust User Credit balances and view transaction audit logs
- Moderate inappropriate Resources or Discussion posts

---

## 11. Non-Functional Requirements

- **Local execution only** via `python manage.py runserver`.
- **Zero paid/cloud dependencies** — SQLite database, local media folder.
- **Upload safety** — Max 10MB, restricted to PDF, PNG, JPG, TXT, DOCX.
- **Automated Seeding** — `python manage.py seed_demo_data` populates realistic test data for instant demoing.

---

## 12. Definition of Done (Demo Checklist)

- [ ] User registration, login, logout, and profile setup with skill tagging
- [ ] RoleAssignment toggling (Mentor, Learner, or Dual-Role)
- [ ] Mentor discovery directory with search, filters, and rule-based match score ranking
- [ ] Mentorship request flow with credit deduction, priority flag, notifications, and accept/reject refund logic
- [ ] Mentorship workspace with session logging and meeting links
- [ ] Discrete milestone checklist with dynamic progress calculation
- [ ] Resource sharing (links, notes, and file uploads up to 10MB) and discussion thread
- [ ] Feedback submission (1–5 star ratings and reviews)
- [ ] Credit wallet with auditable transaction history
- [ ] 5 starter badges auto-awarded on event triggers
- [ ] Dynamic overall leaderboard reflecting real-time scores
- [ ] In-app notification center with unread count
- [ ] One-click Demo Role/User switcher for seamless live evaluation
- [ ] `seed_demo_data` command operational
- [ ] Runs cleanly from scratch with `pip install -r requirements.txt`, `python manage.py migrate`, `python manage.py runserver`
