# Phase 3: Mentorship Lifecycle, Workspace, Sessions & Milestones

## 1. Overview & Objective
Phase 3 builds the operational heart of **MentorPulse**: the collaborative space where a learner and mentor interact. This covers the full lifecycle — from initial request and acceptance to session scheduling, milestone completion, resource sharing, discussion comments, and mentorship completion with a print-ready certificate.

By the end of Phase 3, users will be able to initiate a mentorship, manage sessions, track progress interactively, share resources, and complete goals together.

---

## 2. Deliverables & Components

### 2.1 `mentorship` App
- **Models**:
  - `Mentorship`: Links `mentor` and `learner`, tracks `status` (`PENDING`, `ACTIVE`, `COMPLETED`, `REJECTED`, `CANCELLED`), `goals`, `is_priority`, and start/end dates.
  - `Session`: Individual scheduled/completed meetings with `date`, `meeting_link` (plain text URL), `notes`, and `is_completed`.
  - `Milestone`: Individual verifiable milestones with `title`, `is_completed`, and `completed_at`.
  - `Progress`: OneToOne with `Mentorship`, tracking `completion_pct` and `skill_score`.
  - `Resource`: Shared learning materials (`LINK`, `FILE`, `NOTE`) with safety validation (max 10MB; PDF, images, docs only).
  - `DiscussionPost`: Simple chronological message feed for the mentorship pair.
- **Views**:
  - `MentorshipRequestView`: Learner requests a mentor (setting goals, optional priority flag).
  - `MentorshipInboxView`: Mentor reviews pending requests to Accept or Reject.
  - `MentorshipWorkspaceView`: Unified collaborative hub with tabs:
    - **Overview**: Goals, status, progress bar, participant details.
    - **Sessions**: Upcoming and past session list + "Log New Session" form.
    - **Milestones**: Interactive checklist with dynamic completion percentage.
    - **Resources**: Uploaded links, notes, and file downloads.
    - **Discussions**: Asynchronous conversation thread.
  - `SessionActionViews`: Create session, toggle complete.
  - `MilestoneActionViews`: Add milestone, toggle completion status.
  - `ResourceCreateView` & `DiscussionCreateView`.
  - `MentorshipCompleteView`: Mark mentorship as completed.
  - `CertificateView`: Clean, print-styled HTML certificate accessible upon completion.

---

## 3. Step-by-Step Implementation Tasks

### Step 1: Create the `mentorship` App & Models
1. Run `python manage.py startapp mentorship`.
2. Define models in `mentorship/models.py` (`Mentorship`, `Session`, `Milestone`, `Progress`, `Resource`, `DiscussionPost`).
3. Add a helper method on `Progress` to recalculate `completion_pct` automatically based on completed milestones and sessions:
   $$\text{completion\_pct} = \left(\frac{\text{completed\_milestones}}{\text{total\_milestones}} \times 70\%\right) + \left(\frac{\text{completed\_sessions}}{\text{target\_sessions}} \times 30\%\right)$$
4. Register models in `mentorship/admin.py`.
5. Run migrations.

### Step 2: Request, Acceptance & Cancellation Flow
1. Create `MentorshipRequestForm` (goals, optional `is_priority` checkbox).
2. Implement learner request view:
   - Validates that learner isn't requesting themselves.
   - Prevents duplicate pending requests to the same mentor.
   - Sets status to `PENDING`.
3. Implement mentor inbox:
   - Displays incoming pending requests.
   - Priority requests feature a distinct **"⭐ Priority Request"** gold highlight badge at the top.
   - Mentor can click **Accept** (`status=ACTIVE`, auto-creates default `Progress` record) or **Reject** (`status=REJECTED`).

### Step 3: Central Mentorship Workspace
1. Build `templates/mentorship/workspace.html`:
   - Header with mentor & learner profile cards, current status badge, and an animated progress bar.
   - Tabbed layout: Sessions, Milestones, Resources, Discussions.
2. Build Session Management:
   - Form modal or inline card to schedule a session (`date`, `meeting_link`, `notes`).
   - "Mark as Completed" button on each session item.
3. Build Milestone Checklist:
   - Add new milestone form.
   - Checkbox toggle endpoint that instantly updates milestone status and recalculates the progress bar.

### Step 4: Resource Sharing & Discussions
1. Implement `ResourceForm` with validation:
   - Rejects files over 10MB or outside approved extensions (PDF, PNG, JPG, TXT, DOCX).
   - Secure file download handler.
2. Implement Discussion post creation:
   - Textarea input submitting to `DiscussionPostCreateView`.
   - Posts render chronologically with author badge, avatar, and timestamp.

### Step 5: Completion & Print-Friendly Certificate
1. Add `MentorshipCompleteView`:
   - Enables either party (or mentor) to finalize the mentorship when milestones are done.
   - Sets `end_date` and `status=COMPLETED`.
2. Create `templates/mentorship/certificate.html`:
   - Framed certificate of completion displaying learner name, mentor name, skills mastered, duration, and a verification timestamp.
   - Formatted with `@media print` CSS so clicking "Print / Save PDF" renders a clean, unblemished certificate.

---

## 4. Verification & Testing Checklist

- [ ] Learner can send a mentorship request with goals and see it listed under their active requests.
- [ ] Mentor sees the request in their inbox (with visual priority badge if flagged).
- [ ] Mentor can accept the request, transitioning status to `ACTIVE`.
- [ ] Both parties can access the Mentorship Workspace.
- [ ] Sessions can be added with date and meeting links; marking complete updates session status.
- [ ] Adding and checking off milestones dynamically updates the workspace progress bar.
- [ ] Uploading an approved file (e.g. PDF under 10MB) attaches it to the workspace; files over 10MB are rejected with an error.
- [ ] Discussion posts appear immediately in chronological order.
- [ ] Completing a mentorship locks the status to `COMPLETED` and unlocks the certificate view.
