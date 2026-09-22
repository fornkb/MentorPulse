from datetime import timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from accounts.models import Skill, Profile, RoleAssignment
from mentorship.models import Mentorship, Session, Milestone, Progress, Resource, DiscussionPost
from gamification.models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry
from gamification.services import CreditService, BadgeService, LeaderboardService
from notifications.models import Notification
from notifications.services import send_notification


class Command(BaseCommand):
    help = "Turnkey seed script: Populates realistic demo users, mentorships, sessions, badges, and leaderboard for MentorPulse live demos."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Starting MentorPulse Phase 5 Demo Data Seeder..."))

        # -------------------------------------------------------------
        # 1. Clean previous demo data for idempotent runs
        # -------------------------------------------------------------
        self.stdout.write("Cleaning previous demo records...")
        demo_usernames = [
            'admin',
            'sarah_backend',
            'marcus_frontend',
            'dr_elena',
            'alex_design',
            'david_devops',
            'alex_learner',
            'priya_learner',
            'jordan_learner',
        ]

        # Delete related objects for these users or existing demo instances
        existing_demo_users = User.objects.filter(username__in=demo_usernames)
        if existing_demo_users.exists():
            Mentorship.objects.filter(mentor__in=existing_demo_users).delete()
            Mentorship.objects.filter(learner__in=existing_demo_users).delete()
            Feedback.objects.filter(given_by__in=existing_demo_users).delete()
            Feedback.objects.filter(given_to__in=existing_demo_users).delete()
            CreditTransaction.objects.filter(user__in=existing_demo_users).delete()
            Credit.objects.filter(user__in=existing_demo_users).delete()
            UserBadge.objects.filter(user__in=existing_demo_users).delete()
            LeaderboardEntry.objects.filter(user__in=existing_demo_users).delete()
            Notification.objects.filter(user__in=existing_demo_users).delete()
            RoleAssignment.objects.filter(user__in=existing_demo_users).delete()
            existing_demo_users.delete()

        # -------------------------------------------------------------
        # 2. Seed Skills
        # -------------------------------------------------------------
        self.stdout.write("Seeding standardized skills taxonomy...")
        skills_catalog = [
            # Programming
            ("Python", "Programming"),
            ("Django", "Programming"),
            ("JavaScript", "Programming"),
            ("TypeScript", "Programming"),
            ("React", "Programming"),
            ("Node.js", "Programming"),
            ("Docker", "Programming"),
            ("Git & GitHub", "Programming"),
            ("PostgreSQL", "Programming"),
            ("Go", "Programming"),

            # Design
            ("UI/UX Design", "Design"),
            ("Figma", "Design"),
            ("Design Systems", "Design"),
            ("User Research", "Design"),
            ("Wireframing", "Design"),

            # Data
            ("Data Science", "Data"),
            ("Machine Learning", "Data"),
            ("SQL & Databases", "Data"),
            ("Deep Learning", "Data"),
            ("Prompt Engineering", "Data"),

            # Business
            ("Product Management", "Business"),
            ("Agile & Scrum", "Business"),
            ("Technical Writing", "Business"),
            ("Career Coaching", "Business"),

            # Other / DevOps
            ("System Design", "Other"),
            ("DevOps & CI/CD", "Other"),
            ("Cloud Architecture", "Other"),
            ("Mock Interviews", "Other"),
        ]

        skill_map = {}
        for name, category in skills_catalog:
            skill, _ = Skill.objects.get_or_create(name=name, defaults={'category': category})
            skill_map[name] = skill

        # -------------------------------------------------------------
        # 3. Seed Core Badges
        # -------------------------------------------------------------
        self.stdout.write("Seeding starter badge definitions...")
        BadgeService.seed_core_badges()

        # -------------------------------------------------------------
        # 4. Create Demo Users (1 Admin, 5 Mentors, 3 Learners)
        # -------------------------------------------------------------
        self.stdout.write("Creating realistic demo accounts...")
        common_password = "DemoPass123!"

        users_specs = [
            # 1. Superuser / Admin
            {
                "username": "admin",
                "email": "admin@mentorpulse.local",
                "first_name": "System",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
                "is_mentor": True,
                "is_learner": True,
                "experience_level": "Expert",
                "availability": "Flexible",
                "skill_score": 9.5,
                "bio": "MentorPulse platform administrator overseeing mentor matching quality, moderation, and system health.",
                "goals": "Ensure a seamless, high-value learning experience across all mentorship cohorts.",
                "skills": ["Python", "Django", "System Design", "PostgreSQL"],
            },
            # 2. Mentor: Sarah Connor (Python & Django Backend)
            {
                "username": "sarah_backend",
                "email": "sarah.backend@mentorpulse.local",
                "first_name": "Sarah",
                "last_name": "Connor",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": True,
                "is_learner": False,
                "experience_level": "Expert",
                "availability": "Weekdays",
                "skill_score": 8.8,
                "bio": "Senior Backend Architect with 8+ years building high-throughput Python and Django microservices. Dedicated to teaching clean architecture, ORM optimization, and robust REST APIs.",
                "goals": "Guide ambitious developers in mastering scalable backend systems and test-driven development.",
                "skills": ["Python", "Django", "PostgreSQL", "Docker", "Git & GitHub", "System Design"],
            },
            # 3. Mentor: Marcus Vance (Frontend & React)
            {
                "username": "marcus_frontend",
                "email": "marcus.frontend@mentorpulse.local",
                "first_name": "Marcus",
                "last_name": "Vance",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": True,
                "is_learner": False,
                "experience_level": "Expert",
                "availability": "Weekends",
                "skill_score": 8.6,
                "bio": "Lead Frontend Engineer and Design Systems creator crafting accessible, ultra-responsive React and TypeScript applications.",
                "goals": "Help engineers master the modern React ecosystem, state architecture, and polished UI design.",
                "skills": ["JavaScript", "TypeScript", "React", "UI/UX Design", "Design Systems"],
            },
            # 4. Mentor: Dr. Elena Rostova (AI & Data Science)
            {
                "username": "dr_elena",
                "email": "dr.elena@mentorpulse.local",
                "first_name": "Elena",
                "last_name": "Rostova",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": True,
                "is_learner": False,
                "experience_level": "Expert",
                "availability": "Flexible",
                "skill_score": 9.2,
                "bio": "AI Researcher & Data Science Lead with a PhD in Applied Mathematics. Mentoring practitioners in end-to-end Machine Learning pipelines and statistical inference.",
                "goals": "Bridge theoretical mathematical foundations with practical, deployable machine learning systems.",
                "skills": ["Data Science", "Machine Learning", "Python", "SQL & Databases", "Deep Learning"],
            },
            # 5. Mentor: Alex Morgan (UI/UX & Product Design)
            {
                "username": "alex_design",
                "email": "alex.design@mentorpulse.local",
                "first_name": "Alex",
                "last_name": "Morgan",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": True,
                "is_learner": False,
                "experience_level": "Advanced",
                "availability": "Weekdays",
                "skill_score": 8.2,
                "bio": "Staff Product Designer passionate about user research, interactive wireframing, and cohesive design systems in Figma.",
                "goals": "Empower engineers and designers to build products that are both intuitive and visually captivating.",
                "skills": ["UI/UX Design", "Figma", "Design Systems", "User Research", "Wireframing"],
            },
            # 6. Mentor: David Kim (DevOps & Cloud)
            {
                "username": "david_devops",
                "email": "david.devops@mentorpulse.local",
                "first_name": "David",
                "last_name": "Kim",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": True,
                "is_learner": False,
                "experience_level": "Advanced",
                "availability": "Flexible",
                "skill_score": 8.0,
                "bio": "Cloud & SRE Specialist focusing on containerization, CI/CD deployment pipelines, and resilient cloud architectures.",
                "goals": "Teach developers how to reliably containerize, automate testing, and deploy web applications.",
                "skills": ["Docker", "DevOps & CI/CD", "Cloud Architecture", "System Design", "Git & GitHub"],
            },
            # 7. Learner: Alex Rivera (Aspiring Python/Django Dev)
            {
                "username": "alex_learner",
                "email": "alex.rivera@mentorpulse.local",
                "first_name": "Alex",
                "last_name": "Rivera",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": False,
                "is_learner": True,
                "experience_level": "Beginner",
                "availability": "Flexible",
                "skill_score": 5.4,
                "bio": "CS graduate seeking hands-on guidance in building scalable Python and Django web applications.",
                "goals": "Master Django ORM, REST APIs, and database indexing for high-performance backend systems.",
                "skills": ["Python", "SQL & Databases"],
            },
            # 8. Learner: Priya Sharma (Frontend Enthusiast)
            {
                "username": "priya_learner",
                "email": "priya.sharma@mentorpulse.local",
                "first_name": "Priya",
                "last_name": "Sharma",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": False,
                "is_learner": True,
                "experience_level": "Intermediate",
                "availability": "Weekends",
                "skill_score": 6.5,
                "bio": "Self-taught web developer transitioning from HTML/CSS to component-driven React applications.",
                "goals": "Master modern React component hierarchy, hooks, state management, and accessible UI design.",
                "skills": ["JavaScript", "React", "UI/UX Design"],
            },
            # 9. Learner: Jordan Lee (Data Science Beginner)
            {
                "username": "jordan_learner",
                "email": "jordan.lee@mentorpulse.local",
                "first_name": "Jordan",
                "last_name": "Lee",
                "is_staff": False,
                "is_superuser": False,
                "is_mentor": False,
                "is_learner": True,
                "experience_level": "Beginner",
                "availability": "Weekdays",
                "skill_score": 4.8,
                "bio": "Junior analyst looking to level up Python skills for data pipelines and predictive modeling.",
                "goals": "Seeking fast-track guidance to transition from basic scripts to production-grade data APIs.",
                "skills": ["Python", "Data Science"],
            },
        ]

        users = {}
        for spec in users_specs:
            user = User.objects.create_user(
                username=spec["username"],
                email=spec["email"],
                first_name=spec["first_name"],
                last_name=spec["last_name"],
                password=common_password,
                is_staff=spec["is_staff"],
                is_superuser=spec["is_superuser"],
            )

            # Update Profile
            profile = user.profile
            profile.experience_level = spec["experience_level"]
            profile.availability = spec["availability"]
            profile.skill_score = spec["skill_score"]
            profile.bio = spec["bio"]
            profile.goals = spec["goals"]
            profile.save()

            for sname in spec["skills"]:
                if sname in skill_map:
                    profile.skills.add(skill_map[sname])

            # Manage Role Assignments
            if spec["is_mentor"]:
                RoleAssignment.objects.create(user=user, role="Mentor", context="Active Mentor Assignment")
            if spec["is_learner"]:
                RoleAssignment.objects.create(user=user, role="Learner", context="Active Learner Assignment")

            # Initialize Wallet
            CreditService.get_or_create_credit(user)

            users[spec["username"]] = user

        # -------------------------------------------------------------
        # 5. Mentorship Scenario A: Active Mentorship with Sessions, Milestones, Resources & Discussions
        # (Sarah Connor & Alex Rivera)
        # -------------------------------------------------------------
        self.stdout.write("Creating Mentorship Scenario 1: Active Mentorship...")
        now = timezone.now()

        m_active = Mentorship.objects.create(
            mentor=users["sarah_backend"],
            learner=users["alex_learner"],
            start_date=(now - timedelta(days=14)).date(),
            status="ACTIVE",
            goals="Master Django ORM, REST APIs, and database indexing for high-performance backend systems.",
            is_priority=False
        )

        # Deduct request fee for Alex
        c_alex = Credit.objects.get(user=users["alex_learner"])
        c_alex.balance -= 10
        c_alex.save()
        CreditTransaction.objects.create(
            user=users["alex_learner"],
            amount=-10,
            reason="SESSION_REQUEST",
            context=f"Mentorship application request fee #{m_active.id}"
        )

        # Session 1 (Completed in past)
        Session.objects.create(
            mentorship=m_active,
            date=now - timedelta(days=7),
            meeting_link="https://meet.google.com/mp-sarah-alex",
            notes="Orientation, query optimization, select_related vs prefetch_related, and indexing strategies.",
            is_completed=True
        )
        # Reward mentor +10 credits
        c_sarah = Credit.objects.get(user=users["sarah_backend"])
        c_sarah.balance += 10
        c_sarah.save()
        CreditTransaction.objects.create(
            user=users["sarah_backend"],
            amount=10,
            reason="SESSION_COMPLETED_REWARD",
            context=f"Completed meeting session #{m_active.id}-1"
        )

        # Session 2 (Upcoming in future)
        Session.objects.create(
            mentorship=m_active,
            date=now + timedelta(days=3),
            meeting_link="https://meet.google.com/mp-sarah-alex",
            notes="Building authenticated REST endpoints with serializers and writing automated unit tests.",
            is_completed=False
        )

        # Milestones (2 of 3 completed => ~67%)
        Milestone.objects.create(
            mentorship=m_active,
            title="Master Django ORM relationships and query optimization",
            is_completed=True,
            completed_at=now - timedelta(days=10)
        )
        Milestone.objects.create(
            mentorship=m_active,
            title="Build clean API views and serialize complex model relations",
            is_completed=True,
            completed_at=now - timedelta(days=4)
        )
        Milestone.objects.create(
            mentorship=m_active,
            title="Implement authentication and write automated test cases",
            is_completed=False,
            completed_at=None
        )

        # Recalculate progress
        p_active, _ = Progress.objects.get_or_create(mentorship=m_active)
        p_active.recalculate()

        # Shared Resources
        Resource.objects.create(
            mentorship=m_active,
            uploaded_by=users["sarah_backend"],
            title="Django Database Optimization Guide",
            type="LINK",
            content="https://docs.djangoproject.com/en/5.2/topics/db/optimization/"
        )
        Resource.objects.create(
            mentorship=m_active,
            uploaded_by=users["sarah_backend"],
            title="Clean Architecture Blueprint",
            type="NOTE",
            content="Separate business logic into domain services and keep Django views lean and focused on HTTP orchestration."
        )

        # Discussions
        DiscussionPost.objects.create(
            mentorship=m_active,
            author=users["sarah_backend"],
            text="Welcome to our mentorship Alex! Looking forward to diving into backend scalability.",
            created_at=now - timedelta(days=14)
        )
        DiscussionPost.objects.create(
            mentorship=m_active,
            author=users["alex_learner"],
            text="Thank you Sarah! I have set up the repository and started profiling ORM queries.",
            created_at=now - timedelta(days=12)
        )
        DiscussionPost.objects.create(
            mentorship=m_active,
            author=users["sarah_backend"],
            text="Fantastic work completing the first two milestones ahead of schedule! Looking forward to our next meeting.",
            created_at=now - timedelta(days=3)
        )

        # -------------------------------------------------------------
        # 6. Mentorship Scenario B: Completed Mentorship with 5-Star Feedback & Certificate
        # (Marcus Vance & Priya Sharma)
        # -------------------------------------------------------------
        self.stdout.write("Creating Mentorship Scenario 2: Completed Mentorship...")
        m_completed = Mentorship.objects.create(
            mentor=users["marcus_frontend"],
            learner=users["priya_learner"],
            start_date=(now - timedelta(days=30)).date(),
            end_date=(now - timedelta(days=2)).date(),
            status="COMPLETED",
            goals="Master modern React component hierarchy, hooks, state management, and accessible UI design.",
            is_priority=False
        )

        # Deduct request fee
        c_priya = Credit.objects.get(user=users["priya_learner"])
        c_priya.balance -= 10
        c_priya.save()
        CreditTransaction.objects.create(
            user=users["priya_learner"],
            amount=-10,
            reason="SESSION_REQUEST",
            context=f"Mentorship application request fee #{m_completed.id}"
        )

        # Completed Sessions (2)
        Session.objects.create(
            mentorship=m_completed,
            date=now - timedelta(days=20),
            meeting_link="https://meet.google.com/mp-marcus-priya",
            notes="Component decomposition, props drilling vs context, and custom hooks.",
            is_completed=True
        )
        Session.objects.create(
            mentorship=m_completed,
            date=now - timedelta(days=5),
            meeting_link="https://meet.google.com/mp-marcus-priya",
            notes="Final capstone review, accessibility audit, and bundle optimization.",
            is_completed=True
        )

        # Reward mentor (+20 credits)
        c_marcus = Credit.objects.get(user=users["marcus_frontend"])
        c_marcus.balance += 20
        c_marcus.save()
        CreditTransaction.objects.create(
            user=users["marcus_frontend"],
            amount=20,
            reason="SESSION_COMPLETED_REWARD",
            context=f"Completed meeting sessions #{m_completed.id}"
        )

        # Completed Milestones (3 of 3 => 100%)
        Milestone.objects.create(
            mentorship=m_completed,
            title="Master React Hooks (useState, useEffect, useMemo)",
            is_completed=True,
            completed_at=now - timedelta(days=22)
        )
        Milestone.objects.create(
            mentorship=m_completed,
            title="Build responsive dashboard layout with dark theme tokens",
            is_completed=True,
            completed_at=now - timedelta(days=12)
        )
        Milestone.objects.create(
            mentorship=m_completed,
            title="Deploy interactive frontend with API integration",
            is_completed=True,
            completed_at=now - timedelta(days=3)
        )

        p_completed, _ = Progress.objects.get_or_create(mentorship=m_completed)
        p_completed.recalculate()

        # Shared Resources
        Resource.objects.create(
            mentorship=m_completed,
            uploaded_by=users["marcus_frontend"],
            title="React 19 Official Documentation & Cheat Sheet",
            type="LINK",
            content="https://react.dev/"
        )
        Resource.objects.create(
            mentorship=m_completed,
            uploaded_by=users["marcus_frontend"],
            title="Accessibility & Design System Guidelines",
            type="NOTE",
            content="Always ensure WCAG 2.1 AA color contrast and full keyboard navigation for interactive components."
        )

        # Mutual 5-Star Feedback
        Feedback.objects.create(
            mentorship=m_completed,
            given_by=users["priya_learner"],
            given_to=users["marcus_frontend"],
            rating=5,
            comment="Marcus is an extraordinary mentor! His explanations of state management and component structure were crystal clear. Highly recommended!"
        )
        Feedback.objects.create(
            mentorship=m_completed,
            given_by=users["marcus_frontend"],
            given_to=users["priya_learner"],
            rating=5,
            comment="Priya demonstrated outstanding dedication and curiosity. She completed every milestone with great attention to detail!"
        )

        # -------------------------------------------------------------
        # 7. Mentorship Scenario C: Pending Priority Request
        # (Jordan Lee -> Sarah Connor)
        # -------------------------------------------------------------
        self.stdout.write("Creating Mentorship Scenario 3: Pending Priority Request...")
        m_pending = Mentorship.objects.create(
            mentor=users["sarah_backend"],
            learner=users["jordan_learner"],
            start_date=now.date(),
            status="PENDING",
            goals="Seeking fast-track guidance to transition from basic scripts to production-grade data APIs and scalable architectures.",
            is_priority=True
        )

        # Deduct 15 credits from Jordan (-10 standard, -5 priority)
        c_jordan = Credit.objects.get(user=users["jordan_learner"])
        c_jordan.balance -= 15
        c_jordan.save()
        CreditTransaction.objects.create(
            user=users["jordan_learner"],
            amount=-10,
            reason="SESSION_REQUEST",
            context=f"Mentorship application request fee #{m_pending.id}"
        )
        CreditTransaction.objects.create(
            user=users["jordan_learner"],
            amount=-5,
            reason="PRIORITY_UNLOCK",
            context="⭐ Fast-track priority queue unlock"
        )

        # -------------------------------------------------------------
        # 8. Evaluate Badges for All Users
        # -------------------------------------------------------------
        self.stdout.write("Evaluating and awarding starter badges...")
        for u in users.values():
            BadgeService.check_and_award_badges(u)

        # -------------------------------------------------------------
        # 9. Recalculate Leaderboard
        # -------------------------------------------------------------
        self.stdout.write("Recalculating real-time platform leaderboard...")
        LeaderboardService.recalculate_leaderboard()

        # -------------------------------------------------------------
        # 10. Seed Realistic In-App Notifications
        # -------------------------------------------------------------
        self.stdout.write("Seeding in-app notifications...")

        # Notifications for Sarah (Mentor)
        send_notification(
            user=users["sarah_backend"],
            message="New mentorship request from Jordan Lee (⭐ Priority).",
            type="REQUEST_RECEIVED",
            link="/mentorships/"
        )
        send_notification(
            user=users["sarah_backend"],
            message="Upcoming meeting session with Alex Rivera in 3 days.",
            type="SESSION_LOGGED",
            link=f"/mentorships/{m_active.id}/"
        )
        send_notification(
            user=users["sarah_backend"],
            message="You earned +10 credits for completing a meeting session with Alex Rivera!",
            type="SESSION_LOGGED",
            link="/wallet/"
        )

        # Notifications for Alex (Learner)
        send_notification(
            user=users["alex_learner"],
            message="Sarah Connor accepted your mentorship request! Workspace is now open.",
            type="REQUEST_ACCEPTED",
            link=f"/mentorships/{m_active.id}/"
        )
        send_notification(
            user=users["alex_learner"],
            message="Milestone 'Build clean API views' completed! Progress is now 67%.",
            type="SESSION_LOGGED",
            link=f"/mentorships/{m_active.id}/"
        )

        # Notifications for Marcus (Mentor)
        send_notification(
            user=users["marcus_frontend"],
            message="You received a 5-star rating and review from Priya Sharma!",
            type="FEEDBACK_RECEIVED",
            link=f"/mentorships/{m_completed.id}/"
        )
        send_notification(
            user=users["marcus_frontend"],
            message="Mentorship with Priya Sharma is COMPLETED. Thank you for guiding your learner!",
            type="SESSION_LOGGED",
            link=f"/mentorships/{m_completed.id}/"
        )

        # Notifications for Priya (Learner)
        send_notification(
            user=users["priya_learner"],
            message="Congratulations! Mentorship with Marcus Vance is COMPLETED! Certificate unlocked.",
            type="SESSION_LOGGED",
            link=f"/mentorships/{m_completed.id}/certificate/"
        )
        send_notification(
            user=users["priya_learner"],
            message="You received a 5-star rating and review from Marcus Vance!",
            type="FEEDBACK_RECEIVED",
            link=f"/mentorships/{m_completed.id}/"
        )

        # Notifications for Jordan (Learner)
        send_notification(
            user=users["jordan_learner"],
            message="Your priority mentorship request was sent to Sarah Connor. Awaiting review.",
            type="REQUEST_RECEIVED",
            link="/mentorships/"
        )

        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write(self.style.SUCCESS("[SUCCESS] MentorPulse Phase 5 Demo Data Seeded Successfully!"))
        self.stdout.write(self.style.SUCCESS("=" * 65))
        self.stdout.write("Demo Accounts Ready (Password: DemoPass123!):")
        self.stdout.write("  * [ADMIN]   admin (System Administrator)")
        self.stdout.write("  * [MENTOR]  sarah_backend (Sarah Connor - Python/Django)")
        self.stdout.write("  * [MENTOR]  marcus_frontend (Marcus Vance - React/Design)")
        self.stdout.write("  * [MENTOR]  dr_elena (Dr. Elena Rostova - AI/Data Science)")
        self.stdout.write("  * [MENTOR]  alex_design (Alex Morgan - UI/UX Design)")
        self.stdout.write("  * [MENTOR]  david_devops (David Kim - DevOps/Cloud)")
        self.stdout.write("  * [LEARNER] alex_learner (Alex Rivera - Active mentorship)")
        self.stdout.write("  * [LEARNER] priya_learner (Priya Sharma - Completed mentorship & cert)")
        self.stdout.write("  * [LEARNER] jordan_learner (Jordan Lee - Pending priority request)")
        self.stdout.write(self.style.SUCCESS("Use the 'Demo Switcher' in the navbar for 1-click instant evaluations!"))

