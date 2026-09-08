from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Skill, Profile, RoleAssignment


class Command(BaseCommand):
    help = "Seed initial skills and test accounts for Phase 1 demo"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Phase 1 skills..."))

        skills_data = [
            # Programming
            ("Python", "Programming"),
            ("JavaScript", "Programming"),
            ("TypeScript", "Programming"),
            ("React", "Programming"),
            ("Django", "Programming"),
            ("Node.js", "Programming"),
            ("Docker", "Programming"),
            ("Git & GitHub", "Programming"),
            ("Go", "Programming"),
            ("Rust", "Programming"),

            # Design
            ("UI/UX Design", "Design"),
            ("Figma", "Design"),
            ("Design Systems", "Design"),
            ("User Research", "Design"),
            ("Wireframing", "Design"),

            # Data
            ("Machine Learning", "Data"),
            ("Data Science", "Data"),
            ("SQL & Databases", "Data"),
            ("Deep Learning", "Data"),
            ("Prompt Engineering", "Data"),

            # Business
            ("Product Management", "Business"),
            ("Agile & Scrum", "Business"),
            ("Technical Writing", "Business"),
            ("Career Coaching", "Business"),

            # Other
            ("System Design", "Other"),
            ("Resume Review", "Other"),
            ("Mock Interviews", "Other"),
        ]

        skill_objs = {}
        created_count = 0
        for name, category in skills_data:
            skill, created = Skill.objects.get_or_create(name=name, defaults={'category': category})
            skill_objs[name] = skill
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f"Successfully processed {len(skills_data)} skills ({created_count} created)."))

        # Create Demo Users
        self.stdout.write(self.style.NOTICE("Seeding demo user accounts..."))

        users_info = [
            {
                "username": "alex_mentor",
                "email": "alex.mentor@example.com",
                "first_name": "Alex",
                "last_name": "Rivera",
                "is_mentor": True,
                "is_learner": False,
                "experience_level": "Expert",
                "availability": "Weekdays",
                "bio": "Senior Backend Architect with 7+ years in Python, distributed microservices, and cloud systems. Passionate about mentoring junior and mid-level devs.",
                "goals": "Help motivated developers master Python, clean architecture, and system design patterns.",
                "skills": ["Python", "Django", "Docker", "Git & GitHub", "System Design"]
            },
            {
                "username": "sara_learner",
                "email": "sara.learner@example.com",
                "first_name": "Sara",
                "last_name": "Chen",
                "is_mentor": False,
                "is_learner": True,
                "experience_level": "Beginner",
                "availability": "Flexible",
                "bio": "CS undergraduate eager to transition into full-stack web development and UI/UX design.",
                "goals": "Build full-stack web applications and master modern UI design in Figma.",
                "skills": ["React", "JavaScript", "UI/UX Design", "Figma"]
            },
            {
                "username": "charlie_dual",
                "email": "charlie.dual@example.com",
                "first_name": "Charlie",
                "last_name": "Kim",
                "is_mentor": True,
                "is_learner": True,
                "experience_level": "Intermediate",
                "availability": "Weekends",
                "bio": "Data Scientist exploring production machine learning systems. I mentor peers in Python/SQL and learn React frontend.",
                "goals": "Mentor aspiring data analysts while developing full-stack frontend capabilities.",
                "skills": ["Python", "Data Science", "SQL & Databases", "Machine Learning", "React"]
            }
        ]

        password = "DemoPass123!"

        for udata in users_info:
            user, u_created = User.objects.get_or_create(
                username=udata["username"],
                defaults={
                    "email": udata["email"],
                    "first_name": udata["first_name"],
                    "last_name": udata["last_name"],
                }
            )
            if u_created:
                user.set_password(password)
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Created user '{user.username}' (password: {password})"))
            else:
                self.stdout.write(f"User '{user.username}' already exists.")

            # Update Profile
            profile = user.profile
            profile.experience_level = udata["experience_level"]
            profile.availability = udata["availability"]
            profile.bio = udata["bio"]
            profile.goals = udata["goals"]
            profile.save()

            # Assign skills
            for sname in udata["skills"]:
                if sname in skill_objs:
                    profile.skills.add(skill_objs[sname])

            # Manage roles
            # Learner
            learner_assignment = user.role_assignments.filter(role="Learner", end_time__isnull=True).first()
            if udata["is_learner"] and not learner_assignment:
                RoleAssignment.objects.create(user=user, role="Learner", context="Demo seed initial role")
            elif not udata["is_learner"] and learner_assignment:
                learner_assignment.delete()

            # Mentor
            mentor_assignment = user.role_assignments.filter(role="Mentor", end_time__isnull=True).first()
            if udata["is_mentor"] and not mentor_assignment:
                RoleAssignment.objects.create(user=user, role="Mentor", context="Demo seed initial role")
            elif not udata["is_mentor"] and mentor_assignment:
                mentor_assignment.delete()

        self.stdout.write(self.style.SUCCESS("Phase 1 seeding complete! Demo credentials available for testing."))
