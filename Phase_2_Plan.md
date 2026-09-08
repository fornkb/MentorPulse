# Phase 2: Skill Catalog, Mentor Discovery & Matching Engine

## 1. Overview & Objective
Phase 2 delivers the discovery core of **MentorPulse**. Learners need an intuitive, searchable directory to browse mentors, filter by criteria (skill tags, availability, experience level), and see mentors ranked according to a deterministic, rule-based matching algorithm.

By the end of Phase 2, a learner will be able to explore all mentors, see a calculated match percentage on each mentor card, and inspect detailed mentor profile pages.

---

## 2. Deliverables & Components

### 2.1 `matching` App
- **Views**:
  - `MentorDirectoryView`: Searchable, filterable list of active mentors.
  - `MentorDetailView`: Public profile view for a mentor showcasing their skills, bio, experience level, availability, badges, and feedback score.
- **Matching Service (`matching/services.py`)**:
  - `calculate_match_score(learner_profile, mentor_profile) -> float`:
    - **Skill Overlap (50%)**: Jaccard similarity or ratio of shared skills between learner goals/skills and mentor skills.
    - **Availability Match (30%)**: Overlap in preferred meeting schedules (e.g. weekdays/weekends/flexible).
    - **Experience Affinity (20%)**: Higher weights when a mentor has higher experience than the learner.
  - `rank_mentors_for_learner(learner, query_params) -> QuerySet / list`: Returns ranked list of mentors annotated with their match score.
- **Templates**:
  - `templates/matching/mentor_list.html`: Responsive grid with search input, skill filter badges, and availability dropdowns.
  - `templates/matching/mentor_detail.html`: Clean mentor profile page with bio, credentials, badges, and a "Request Mentorship" CTA.
  - `templates/matching/components/mentor_card.html`: Reusable mentor card displaying avatar, name, skills pills, match score pill, and rating summary.

---

## 3. Step-by-Step Implementation Tasks

### Step 1: Create the `matching` App
1. Run `python manage.py startapp matching`.
2. Register `matching` in `INSTALLED_APPS`.
3. Configure URL routes in `matching/urls.py` (`/mentors/`, `/mentors/<int:user_id>/`).

### Step 2: Implement the Rule-Based Matching Algorithm
1. Create `matching/services.py`:
   - Parse learner's selected skills and compare against mentor's skills.
   - Evaluate availability compatibility.
   - Score experience level alignment (e.g. Beginner learner paired with Intermediate/Advanced mentor = optimal).
   - Normalize the final score into a `0% - 100%` match percentage.
2. Ensure the algorithm degrades gracefully if a learner has not set up their profile yet (defaults to sorting by skill_score or name).

### Step 3: Build Search & Filtering Views
1. Implement `MentorDirectoryView`:
   - Filter only users with active `RoleAssignment(role='Mentor')`.
   - Support query parameters: `?q=`, `?skill=`, `?experience=`, `?availability=`.
   - Annotate or attach the computed match score when a learner is authenticated.
2. Implement `MentorDetailView`:
   - Fetch mentor profile, active role assignment, and associated skills.
   - Ensure learners can view mentor details, but mentors viewing their own profile see an "Edit Profile" shortcut.

### Step 4: Template Design & Polish
1. Build `mentor_list.html` with an engaging filter bar:
   - Clickable skill pill filters.
   - Search input with clear button.
   - Card grid with hover states and vibrant "95% Match" pill tags.
2. Build `mentor_detail.html` with clear calls to action and organized sections (About, Skills Taught, Schedule, Achievements).

---

## 4. Verification & Testing Checklist

- [ ] Unauthenticated guests and logged-in learners can view the mentor directory at `/mentors/`.
- [ ] Only users with an active `Mentor` role assignment appear in the mentor directory.
- [ ] Filtering by skill tag returns only mentors possessing that skill.
- [ ] Matching score calculates accurately (e.g., mentor sharing 3 out of 3 of the learner's desired skills ranks higher than a mentor sharing 1).
- [ ] Empty state renders gracefully when no mentors match the search query.
- [ ] Mentor detail page renders all skills, bio, and availability clearly.
