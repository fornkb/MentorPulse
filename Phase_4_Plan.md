# Phase 4: Credit Economy, Feedback, Badges & Leaderboard

## 1. Overview & Objective
Phase 4 layers the motivational and economic engine onto **MentorPulse**. It implements the closed-loop **Credit System**, auditable transaction ledger, post-session/mentorship **Feedback & Ratings**, auto-awarded **Badges**, and the real-time **Leaderboard**.

By the end of Phase 4, actions taken across the platform (requesting mentorships, logging sessions, sharing resources, and completing mentorships) will directly earn credits, unlock achievements, update feedback ratings, and drive user positions on the leaderboard.

---

## 2. Deliverables & Components

### 2.1 `gamification` App
- **Models**:
  - `Credit`: OneToOne with `User`, tracking available balance (default starting: 50).
  - `CreditTransaction`: Auditable log with `amount`, `reason` (`STARTING_BONUS`, `SESSION_REQUEST`, `SESSION_REFUND`, `SESSION_COMPLETED_REWARD`, `PRIORITY_UNLOCK`, `ADMIN_ADJUSTMENT`), and timestamp.
  - `Feedback`: 1–5 star rating and comments linked to a `Mentorship`, tracking `given_by` and `given_to`.
  - `Badge`: Definition table (`name`, `description`, `icon`).
  - `UserBadge`: Relationship table linking `User` and awarded `Badge` with `earned_date`.
  - `Leaderboard` & `LeaderboardEntry`: Precomputed ranking table storing `user`, `score`, and `rank`.
- **Services (`gamification/services.py`)**:
  - `CreditService`:
    - `deduct_for_request(learner, is_priority=False) -> bool`: Checks balance (10 or 15 credits) and logs transaction.
    - `refund_for_rejection(learner, is_priority=False)`: Restores credits upon mentor rejection.
    - `reward_for_session(mentor)`: Awards +10 credits upon completed session.
  - `BadgeService`:
    - `check_and_award_badges(user)`: Evaluates rules for the 5 starter badges (`First Steps`, `Committed Mentor`, `Rising Star`, `Top Rated`, `Helpful Hand`).
  - `LeaderboardService`:
    - `recalculate_leaderboard()`: Recomputes overall scores:
      $$\text{Score} = \text{skill\_score} + (\text{credit\_balance} \times 0.5) + (\text{badge\_count} \times 10)$$
      Assigns consecutive ranks (1st, 2nd, 3rd, etc.).
- **Views & Templates**:
  - `WalletView` (`templates/gamification/wallet.html`): Displays balance card and transaction history table.
  - `FeedbackModal/Form` (`templates/gamification/feedback_form.html`): Interactive 5-star rating selector and comment box.
  - `LeaderboardView` (`templates/gamification/leaderboard.html`): Sleek podium top-3 cards + full ranked table with search.
  - `BadgesView` (`templates/gamification/badges.html`): Profile achievement showcase showing unlocked badges in color and locked ones in greyscale.

---

## 3. Step-by-Step Implementation Tasks

### Step 1: Create the `gamification` App & Models
1. Run `python manage.py startapp gamification`.
2. Define models in `gamification/models.py`.
3. Register models in `gamification/admin.py` with custom filters and search fields (staff can adjust balances directly).
4. Run migrations.

### Step 2: Implement the Credit System & Transaction Ledger
1. Connect Django signal `post_save` on `User` to auto-create `Credit` with initial 50 credits and log a `STARTING_BONUS` transaction.
2. Hook `CreditService` into the Phase 3 request flow:
   - When a learner clicks "Request Mentorship", verify they have $\ge 10$ credits (or $\ge 15$ if Priority is checked).
   - If insufficient, halt request and display an alert prompt: *"Insufficient credits. Earn credits by mentoring others or completing sessions."*
   - If sufficient, deduct credits and create `CreditTransaction`.
3. Hook refund logic:
   - If mentor clicks **Reject**, immediately refund the deducted amount with reason `SESSION_REFUND`.
4. Hook reward logic:
   - When a session is marked complete, mentor receives +10 credits with reason `SESSION_COMPLETED_REWARD`.

### Step 3: Feedback & Rating System
1. Build `FeedbackForm` with star selector (1 to 5) and comments.
2. Allow feedback submission from the Mentorship Workspace.
3. Compute average rating on mentor and learner profiles, displayed with a star icon and review count.

### Step 4: Badge Auto-Award Engine
1. Pre-seed badge definitions:
   - **First Steps**: Completed 1st mentorship.
   - **Committed Mentor**: Completed 5 mentorships as a mentor.
   - **Rising Star**: `skill_score > 80`.
   - **Top Rated**: Average rating $\ge 4.5$ with at least 5 reviews.
   - **Helpful Hand**: Shared 5+ resources across mentorships.
2. In `BadgeService`, implement synchronous check functions triggered on session completion, resource upload, feedback submission, and mentorship completion.
3. Prevent duplicate badge awards (`UserBadge.objects.get_or_create`).

### Step 5: Leaderboard Computation
1. Implement `recalculate_leaderboard()` in `gamification/services.py`.
2. Re-trigger recalculation whenever points, badges, or skill scores change.
3. Build `leaderboard.html` with a podium layout for 1st, 2nd, 3rd places and an annotated table for remaining participants.

---

## 4. Verification & Testing Checklist

- [ ] New user registration automatically provisions 50 credits and an initial `STARTING_BONUS` transaction.
- [ ] Learner with < 10 credits is blocked from submitting mentorship requests.
- [ ] Sending a request deducts 10 credits (or 15 if priority is checked) and records `SESSION_REQUEST` / `PRIORITY_UNLOCK`.
- [ ] Rejecting a request refunds credits to the learner with a `SESSION_REFUND` transaction.
- [ ] Completing a session awards the mentor +10 credits with a `SESSION_COMPLETED_REWARD` transaction.
- [ ] Submitting feedback updates the recipient's average rating.
- [ ] Completing a first mentorship automatically unlocks the "First Steps" badge.
- [ ] Leaderboard accurately ranks users according to the formula and displays top scores on `/leaderboard/`.
- [ ] Django Admin displays all transactions and allows manual credit adjustments.
