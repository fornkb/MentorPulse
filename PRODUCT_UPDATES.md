# Product improvements

The interface now uses a light neutral palette, a muted green accent, simpler navigation, and layouts that adapt to desktop and mobile. These changes retain the working product flows below.

## Daily use

- The dashboard shows active mentorships and their progress, incoming and outgoing request counts, wallet credits, upcoming meetings, and unfinished milestones.
- Profiles separate skills users can teach or showcase from skills they want to learn. Existing learners' selections are copied into learning targets by a data migration.
- Mentor discovery uses learning targets for matching. It includes reviews, verified badges, portfolio links, mentor capacity, saved mentors, and filters for verified mentors or those accepting learners.
- Profile settings include a time zone, portfolio URL, and maximum active mentorship capacity. Time zones affect meeting entry, display, and reminders.
- Mentors can publish weekly availability windows. With no published windows, participants can agree on any free time. Publishing windows limits future bookings to those windows and leaves existing meetings intact.
- Sessions support 15–240 minute durations, rescheduling, cancellation, and per-session calendar downloads. Bookings check both participants' sessions across mentorships for conflicts. Calendar timestamps use UTC.
- Milestones support editing and optional deadlines. Form errors retain submitted values. Completed workspaces are read-only; reviews remain available to participants.
- Uploaded resources use participant-checked downloads. Web resources accept HTTP/HTTPS links only.

## Credits and completion

- A request, its charge, ledger entries, and notification commit together or roll back together.
- Conditional database updates prevent wallet overdrafts and lost balance updates. Wallet balances also have a nonnegative database constraint.
- Unique event keys make refunds and session rewards safe to retry. Duplicate open mentorships and duplicate participant reviews are prevented by database constraints.
- Lifecycle operations serialize participant changes and retry brief SQLite lock contention. SQLite remains suitable for the local demo; concurrent multi-user deployment should use a server database and validate concurrency there too.
- Only the mentor can confirm an ended session as completed. Confirmation is final and earns its reward once.
- Only the mentor can approve mentorship completion. At least one milestone and one non-cancelled session must be completed, all milestones must be finished, and remaining sessions must be completed or cancelled.
- Certificates have a stable UUID, a public verification page, and a private PDF download. Issued learner/mentor names and skills are stored as a snapshot, so later profile changes do not change a credential. A verification link exposes the credential holder's name, mentor, completion date, and skills to anyone who has the link.
- Existing completed certificates are preserved during migration. They were issued under the previous rules; new completion requirements apply to new approvals.

## Accounts and review

- Password recovery and password changes use Django's standard account tokens and password validation.
- Email-verification links expire after 24 hours and are bound to the current email address. Changing the address resets verification. Resending has a one-minute session cooldown.
- Mentors submit experience and evidence for verification. Administrators review requests under **Profiles** in Django Admin and use the approve/decline actions. Users cannot set their own verified status through profile settings.
- Profile reports are stored privately under **User reports** in Django Admin, with status and staff notes for review.
- Account settings link to security, notification preferences, mentor verification, and availability.

## Email delivery

The local default is Django's console email backend: verification and password-reset emails appear in the server terminal. It does not deliver email to inboxes until SMTP is configured.

Set these environment variables before starting the app:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=your-mail-provider-host
EMAIL_PORT=587
EMAIL_USE_TLS=true
EMAIL_HOST_USER=your-mail-account
EMAIL_HOST_PASSWORD=your-mail-provider-password
DEFAULT_FROM_EMAIL=your-verified-sender-address
SITE_URL=https://your-mentorpulse-domain
```

For tests, use the local-memory backend provided by the test settings. Keep real mail credentials out of source control.

## Reminders and inbox updates

The unread notification counter refreshes every 30 seconds while the page is visible. The full inbox and previews refresh when navigating or reloading.

Users can choose optional session updates, upcoming-session reminders, discussions, and achievement notifications. Request decisions and reviews remain enabled.

The Windows launcher starts the reminder-enabled development server. It checks every minute for sessions starting in the next 24 hours and sends each participant one inbox reminder. Rescheduling resets reminder eligibility; completed and cancelled meetings are skipped.

```bash
python manage.py runserver_with_reminders
```

For deployment, run the idempotent reminder command hourly using the host's scheduler, alongside a production web server:

```bash
python manage.py send_session_reminders
```

## Demo data

Starting the demo preserves existing demo accounts and their activity. If any named demo account exists, normal seeding does not replace or delete it. A fresh database still gets the complete demo.

Only an explicit reset deletes and recreates those named accounts and their related activity:

```bash
python manage.py seed_demo_data --reset-demo
```

This reset is intended for disposable demonstration data. Demo seeding is disabled outside debug mode.

## Verification

Install the updated requirements, apply migrations, and run the complete test suite:

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py test --settings=mentorpulse.test_settings
```

The suite includes transaction rollback, concurrent spending and refunds, duplicate requests, capacity, completion permissions, frozen credentials, scheduling boundaries and conflicts, time zones, calendar escaping, reminder retries, account tokens, saved mentors, and private downloads.

The test settings only change password hashing speed, the email backend, and the upload directory. They must not be used to run the application.

## Frontend refresh

- Main navigation focuses on Dashboard, Find mentors, and Mentorships. Wallet, notifications, demo accounts, account settings, and community features remain available.
- The dashboard puts active mentorships, upcoming meetings, and next tasks first, with fewer competing actions.
- Mentor search combines search, skill selection, and optional filters in one form. Cards show expertise, reviews, and match fit without decorative score widgets.
- Profiles, account forms, notifications, credits, achievements, and certificates share calmer colors, readable typography, and consistent controls.
- Workspace tabs support direct links to sessions and milestones. Mobile tabs scroll inside their own row, while session actions wrap to fit the screen.
- Keyboard focus remains visible. Decorative icons are hidden from screen readers, and navigation and form controls have labels.
