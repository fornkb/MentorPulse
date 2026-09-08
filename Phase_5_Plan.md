# Phase 5: Notification Center, Demo Seeder, Demo Switcher & Final Polish

## 1. Overview & Objective
Phase 5 brings **MentorPulse** to full completion and demo readiness. It implements the in-app **Notification Center**, the **One-Click Demo Role/User Switcher** for live evaluations, the automated **Demo Data Seeder**, and comprehensive UI/UX polish across the entire application.

By the end of Phase 5, the project will be 100% turnkey: clonable on any machine, populated with realistic data in one command (`python manage.py seed_demo_data`), and immediately presentable with smooth demo user switching.

---

## 2. Deliverables & Components

### 2.1 `notifications` App
- **Model**:
  - `Notification`: Stores `user`, `message`, `type` (`REQUEST_RECEIVED`, `REQUEST_ACCEPTED`, `REQUEST_REJECTED`, `SESSION_LOGGED`, `FEEDBACK_RECEIVED`, `BADGE_EARNED`), `is_read`, `link`, and `created_at`.
- **Helper Utility (`notifications/services.py`)**:
  - `send_notification(user, message, type, link="")`: Central function called by event handlers across the platform.
- **Views & UI**:
  - Context processor providing `unread_notification_count` to the top navbar on every page.
  - Navbar bell dropdown showing recent notifications and an unread badge.
  - Full notifications inbox view (`templates/notifications/list.html`) with "Mark all as read" capability.

### 2.2 Live Demo Utilities
- **One-Click Demo User Switcher**:
  - A convenient top-bar dropdown (rendered when `DEBUG=True`) allowing instant switching between demo accounts (e.g. `Sarah (Mentor)`, `Alex (Learner)`, `Admin`) without logging out and re-entering credentials.
- **Demo Data Seeder (`accounts/management/commands/seed_demo_data.py`)**:
  - A single command (`python manage.py seed_demo_data`) that clears test data and populates:
    - 1 Superuser / Admin.
    - 5 Distinct Mentors (e.g., Python Backend, Frontend React, AI/Data Science, UI/UX Design, DevOps) with realistic bios, skills, and schedules.
    - 3 Learners with different goals.
    - 1 Active Mentorship with logged sessions, completed milestones, resources, and discussions.
    - 1 Completed Mentorship with 5-star feedback and an unlocked certificate.
    - 1 Pending Priority Mentorship request in the mentor's inbox.
    - Pre-awarded badges and an active, populated leaderboard.

### 2.3 UI/UX Polish & Empty States
- Custom 404/500 error pages.
- Polished empty states with illustrations/icons (e.g., "No pending requests", "No sessions scheduled yet", "You have zero unread notifications").
- Toast notifications for user interactions (e.g. "Milestone completed!", "Meeting link copied").

---

## 3. Step-by-Step Implementation Tasks

### Step 1: Implement the `notifications` App
1. Run `python manage.py startapp notifications`.
2. Define `Notification` model and migrate database.
3. Write `notifications/services.py` with `send_notification()`.
4. Connect notifications to event triggers:
   - Mentorship requested $\rightarrow$ Notify Mentor.
   - Mentorship accepted / rejected $\rightarrow$ Notify Learner.
   - Session logged / marked complete $\rightarrow$ Notify both parties.
   - Feedback received $\rightarrow$ Notify recipient.
   - Badge awarded $\rightarrow$ Notify user.
5. Create context processor `notifications.context_processors.unread_notifications` and register in `settings.py`.
6. Build navbar bell dropdown and `/notifications/` page.

### Step 2: Build the One-Click Demo User Switcher
1. Create a lightweight development endpoint `/switch-user/<int:user_id>/` enabled only when `DEBUG=True`.
2. Add a styled "⚡ Demo Switcher" pill in the navigation bar listing pre-seeded demo users.
3. Clicking a user switches session authentication instantly and redirects to their dashboard.

### Step 3: Implement the `seed_demo_data` Management Command
1. Create `accounts/management/commands/seed_demo_data.py`.
2. Implement structured creation logic:
   - Create skills: `Python`, `Django`, `JavaScript`, `React`, `UI/UX`, `Data Science`, `PostgreSQL`.
   - Create starter badges: `First Steps`, `Committed Mentor`, `Rising Star`, `Top Rated`, `Helpful Hand`.
   - Create test users with realistic profiles, profile photos, and role assignments.
   - Create mock credit transactions, mentorships, sessions, milestones, discussions, and ratings.
   - Recompute leaderboard so ranks are immediately populated.

### Step 4: UI/UX Audit & Polish
1. Audit all screens for visual consistency:
   - Check responsive layouts on mobile, tablet, and desktop viewports.
   - Ensure color contrast and badge styles match the modern design tokens.
   - Verify that all forms display friendly field-level validation errors.
2. Ensure every list view has a clean empty state with an actionable button (e.g. "Browse Mentors" or "Set Availability").

---

## 4. Verification & Testing Checklist

- [ ] Triggering events across the system generates corresponding notifications in the recipient's bell menu.
- [ ] Clicking a notification navigates to the relevant page (e.g. directly to the mentorship workspace) and marks it as read.
- [ ] Navbar bell shows real-time unread badge count.
- [ ] One-Click Demo Switcher allows switching between Mentor and Learner in under 1 second.
- [ ] Running `python manage.py seed_demo_data` executes cleanly on an empty or existing SQLite database without errors.
- [ ] Demo mentors, learners, active sessions, badges, and leaderboard populate immediately.
- [ ] Full end-to-end user journey works without page errors:
  1. Learner browses mentors and inspects match score.
  2. Learner sends priority request (-15 credits).
  3. Mentor switches in via switcher, sees priority tag, and accepts.
  4. Both parties log session, complete milestone, and upload a resource.
  5. Session marked complete (+10 credits to mentor, badge check triggered).
  6. Feedback submitted and mentorship marked complete.
  7. Certificate generated and viewed.
  8. Leaderboard reflects updated ranks.
