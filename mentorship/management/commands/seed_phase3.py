from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from mentorship.models import Mentorship, Progress, Session, Milestone, Resource, DiscussionPost


class Command(BaseCommand):
    help = "Seed realistic mentorships, sessions, milestones, resources, and discussions for Phase 3 demo"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Phase 3 mentorship lifecycle scenarios..."))

        # Fetch test accounts
        try:
            sara = User.objects.get(username='sara_learner')
            david = User.objects.get(username='david_frontend')
            maya = User.objects.get(username='maya_design')
            alex = User.objects.get(username='alex_mentor')
            charlie = User.objects.get(username='charlie_dual')
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"Error fetching seed users: {e}. Run seed_phase1 and seed_phase2 first."))
            return

        # ----------------------------------------------------
        # Scenario 1: Active Mentorship (Sara Chen & David Vance)
        # ----------------------------------------------------
        m1, created1 = Mentorship.objects.get_or_create(
            learner=sara,
            mentor=david,
            defaults={
                'status': 'ACTIVE',
                'goals': 'Master modern React architecture, TypeScript patterns, and component libraries.',
                'is_priority': True,
                'start_date': timezone.now().date() - timedelta(days=14),
            }
        )
        if not created1:
            m1.status = 'ACTIVE'
            m1.save()

        p1, _ = Progress.objects.get_or_create(mentorship=m1)

        # Milestones
        m1.milestones.all().delete()
        Milestone.objects.create(
            mentorship=m1,
            title='Setup component design tokens & Storybook workflow',
            is_completed=True,
            completed_at=timezone.now() - timedelta(days=8)
        )
        Milestone.objects.create(
            mentorship=m1,
            title='Implement compound modal & dropdown component variants',
            is_completed=True,
            completed_at=timezone.now() - timedelta(days=3)
        )
        Milestone.objects.create(
            mentorship=m1,
            title='Performance profiling & custom rendering hooks optimization',
            is_completed=False
        )

        # Sessions
        m1.sessions.all().delete()
        Session.objects.create(
            mentorship=m1,
            date=timezone.now() - timedelta(days=7),
            meeting_link='https://meet.google.com/abc-xyz-demo',
            notes='Kickoff session covering component hierarchy and folder conventions.',
            is_completed=True
        )
        Session.objects.create(
            mentorship=m1,
            date=timezone.now() + timedelta(days=3),
            meeting_link='https://meet.google.com/abc-xyz-demo',
            notes='Deep dive into custom React hooks, memoization pitfalls, and state machines.',
            is_completed=False
        )

        # Resources
        m1.resources.all().delete()
        Resource.objects.create(
            mentorship=m1,
            uploaded_by=david,
            title='Modern React Architecture & Component Design Guide',
            type='LINK',
            content='https://react.dev/learn/thinking-in-react'
        )
        Resource.objects.create(
            mentorship=m1,
            uploaded_by=david,
            title='Key Session Takeaways & State Management Rules',
            type='NOTE',
            content="1. Prefer composition over props drilling.\n2. Keep state as local as possible.\n3. Colocate component tests right next to source files."
        )

        # Discussions
        m1.discussion_posts.all().delete()
        DiscussionPost.objects.create(
            mentorship=m1,
            author=david,
            text="Welcome to the mentorship Sara! Let's start with setting up the component tokens.",
            created_at=timezone.now() - timedelta(days=12)
        )
        DiscussionPost.objects.create(
            mentorship=m1,
            author=sara,
            text="Thanks David! I've completed milestone 1 and pushed the storybook repo.",
            created_at=timezone.now() - timedelta(days=6)
        )
        DiscussionPost.objects.create(
            mentorship=m1,
            author=david,
            text="Awesome progress on the compound components. Let's review them in our session on Thursday!",
            created_at=timezone.now() - timedelta(days=2)
        )

        p1.recalculate()
        self.stdout.write(self.style.SUCCESS(f"Scenario 1 Seeded: Active Mentorship (Sara & David) — Progress: {p1.completion_pct}%"))

        # ----------------------------------------------------
        # Scenario 2: Pending Priority Request (Sara Chen -> Maya Lin)
        # ----------------------------------------------------
        m2, created2 = Mentorship.objects.get_or_create(
            learner=sara,
            mentor=maya,
            defaults={
                'status': 'PENDING',
                'goals': 'I want to master design systems in Figma, design tokens, and user research frameworks for enterprise applications.',
                'is_priority': True,
                'start_date': timezone.now().date(),
            }
        )
        self.stdout.write(self.style.SUCCESS("Scenario 2 Seeded: Pending Priority Request (Sara -> Maya)"))

        # ----------------------------------------------------
        # Scenario 3: Completed Mentorship (Charlie Kim & Alex Rivera)
        # ----------------------------------------------------
        m3, created3 = Mentorship.objects.get_or_create(
            learner=charlie,
            mentor=alex,
            defaults={
                'status': 'COMPLETED',
                'goals': 'Master distributed Python backend systems, microservices design, and container deployment.',
                'is_priority': False,
                'start_date': timezone.now().date() - timedelta(days=60),
                'end_date': timezone.now().date() - timedelta(days=5),
            }
        )
        if not created3:
            m3.status = 'COMPLETED'
            m3.end_date = timezone.now().date() - timedelta(days=5)
            m3.save()

        p3, _ = Progress.objects.get_or_create(mentorship=m3)
        m3.milestones.all().delete()
        Milestone.objects.create(
            mentorship=m3,
            title='Architecture blueprint for distributed task queues',
            is_completed=True,
            completed_at=timezone.now() - timedelta(days=40)
        )
        Milestone.objects.create(
            mentorship=m3,
            title='Database indexing and caching strategies with Redis',
            is_completed=True,
            completed_at=timezone.now() - timedelta(days=20)
        )
        Milestone.objects.create(
            mentorship=m3,
            title='Containerized deployment with automated health checks',
            is_completed=True,
            completed_at=timezone.now() - timedelta(days=5)
        )
        p3.recalculate()
        self.stdout.write(self.style.SUCCESS("Scenario 3 Seeded: Completed Mentorship (Charlie & Alex) — Certificate Unlocked!"))

        self.stdout.write(self.style.SUCCESS("Phase 3 mentorship scenarios successfully populated!"))
