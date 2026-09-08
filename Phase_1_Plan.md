# Phase 1: Foundation, Design System & User Accounts

## 1. Overview & Objective
Phase 1 establishes the foundational infrastructure of the **MentorPulse** platform. It sets up the Django 5 project, SQLite database, shared templates, and the complete user account system with skills and dual-role assignments (Mentor/Learner).

By the end of Phase 1, any user will be able to register, log in, manage their profile with skill tags, select their active roles, and view their personal dashboard within a polished, responsive UI shell.

---

## 2. Deliverables & Components

### 2.1 Project Core
- **Django Project**: `mentorpulse` with standard configuration for static/media files, SQLite database, and security settings.
- **Design System**: Responsive layout using modern CSS variables, Bootstrap 5 (via CDN), Inter typography, card surfaces, form styling, and alert messages.

### 2.2 `accounts` App
- **Models**:
  - `Skill`: Normalized skill model (`name`, `category`).
  - `Profile`: OneToOne with Django's `User`, ManyToMany with `Skill`, fields for `goals`, `experience_level`, `availability`, `skill_score`, and `bio`.
  - `RoleAssignment`: Tracks active roles (`Mentor` and/or `Learner`) with timestamps and optional context.
- **Forms**:
  - `UserRegistrationForm`: Username, email, password, confirm password.
  - `UserLoginForm`: Authentication form with clean styling.
  - `ProfileEditForm`: Skills multi-select, bio, experience level, availability, goals.
  - `RoleToggleForm`: Switch or activate Mentor / Learner roles.
- **Views**:
  - `RegisterView` / `LoginView` / `LogoutView`.
  - `ProfileView` & `ProfileEditView`.
  - `DashboardView`: Role-aware landing screen for logged-in users.

---

## 3. Step-by-Step Implementation Tasks

### Step 1: Project Initialization & Environment Setup
1. Initialize virtual environment and install dependencies: `django>=5.0`, `pillow`.
2. Generate Django project: `django-admin startproject mentorpulse .`.
3. Configure `mentorpulse/settings.py`:
   - Setup `STATIC_URL`, `STATICFILES_DIRS`, `MEDIA_URL`, `MEDIA_ROOT`.
   - Register apps: `accounts`.
   - Configure message tags for alert styling.

### Step 2: Build the Core Design System & Base Layout
1. Create `templates/base.html`:
   - Modern meta tags, Inter font from Google Fonts, Bootstrap 5 CDN, custom CSS variables.
   - Dynamic top navigation bar (logo, links, notifications placeholder, user avatar & dropdown).
   - Global Django flash messages container (success, error, warning, info).
   - Clean footer.
2. Create `static/css/main.css`:
   - Theme variables: primary slate/indigo palette, clean borders, rounded card tokens, smooth transitions.

### Step 3: Implement the `accounts` Models & Migrations
1. Define `Skill` model in `accounts/models.py`.
2. Define `Profile` model with signal (`post_save` on `User` to auto-create `Profile`).
3. Define `RoleAssignment` model with helper properties on `User` or `Profile` (`is_mentor`, `is_learner`).
4. Register all models in `accounts/admin.py` with search and filter fields.
5. Create and execute database migrations.

### Step 4: Auth & Profile Forms & Views
1. Build authentication templates:
   - `templates/accounts/login.html`
   - `templates/accounts/register.html`
2. Build profile management templates:
   - `templates/accounts/profile_edit.html`
   - `templates/accounts/dashboard.html`
3. Connect URLs in `accounts/urls.py` and mount onto `mentorpulse/urls.py`.

---

## 4. Verification & Testing Checklist

- [ ] Project boots cleanly via `python manage.py runserver` without migration errors.
- [ ] New user registration successfully creates `User` and linked `Profile`.
- [ ] User can log in and log out with appropriate session persistence and redirect messages.
- [ ] User can add/edit skills, select experience level, and update goals.
- [ ] User can assign themselves as a Mentor, Learner, or both.
- [ ] Django Admin (`/admin/`) allows viewing and editing Users, Profiles, Skills, and RoleAssignments.
- [ ] Responsive UI renders cleanly on mobile and desktop viewports.
