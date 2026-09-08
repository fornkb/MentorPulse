from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from accounts.models import Skill, Profile, RoleAssignment


class Command(BaseCommand):
    help = "Seed diverse mentor profiles for Phase 2 discovery and matching demo"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding Phase 2 mentor directory..."))

        # Map skills
        all_skills = {s.name: s for s in Skill.objects.all()}

        mentors_data = [
            {
                "username": "maya_design",
                "email": "maya.design@example.com",
                "first_name": "Maya",
                "last_name": "Lin",
                "experience_level": "Expert",
                "availability": "Flexible / Evenings",
                "skill_score": 9.4,
                "bio": "Principal Product Designer with 8+ years leading design systems at top tech scale-ups. Passionate about human-centered design, user research, and accessible interfaces.",
                "goals": "Mentor aspiring UI/UX designers and front-end engineers in mastering Figma and design system tokens.",
                "skills": ["UI/UX Design", "Figma", "Design Systems", "User Research", "Wireframing"]
            },
            {
                "username": "david_frontend",
                "email": "david.frontend@example.com",
                "first_name": "David",
                "last_name": "Vance",
                "experience_level": "Advanced",
                "availability": "Weekdays",
                "skill_score": 8.9,
                "bio": "Staff Frontend Engineer specializing in React, TypeScript, and modern state architectures. Active open-source contributor.",
                "goals": "Help developers master full-stack React, component libraries, and clean UI engineering.",
                "skills": ["React", "JavaScript", "TypeScript", "UI/UX Design", "Git & GitHub"]
            },
            {
                "username": "priya_ai",
                "email": "priya.ai@example.com",
                "first_name": "Priya",
                "last_name": "Sharma",
                "experience_level": "Expert",
                "availability": "Weekends",
                "skill_score": 9.6,
                "bio": "AI Research Scientist and Machine Learning Engineer. I guide engineers transitioning into Deep Learning, PyTorch, and generative AI prompt engineering.",
                "goals": "Coach developers through practical data science workflows, model evaluation, and LLM implementations.",
                "skills": ["Python", "Machine Learning", "Data Science", "Deep Learning", "Prompt Engineering", "SQL & Databases"]
            },
            {
                "username": "marcus_cloud",
                "email": "marcus.cloud@example.com",
                "first_name": "Marcus",
                "last_name": "Aurelius",
                "experience_level": "Advanced",
                "availability": "Weekdays",
                "skill_score": 8.7,
                "bio": "DevOps & Cloud Systems Architect. 6 years scaling containerized microservices, CI/CD pipelines, and high-availability Linux infrastructure.",
                "goals": "Mentor developers on Docker, Go, system architecture, and production readiness.",
                "skills": ["Docker", "System Design", "Go", "Git & GitHub", "Python"]
            },
            {
                "username": "sarah_product",
                "email": "sarah.product@example.com",
                "first_name": "Sarah",
                "last_name": "Jenkins",
                "experience_level": "Advanced",
                "availability": "Flexible / Evenings",
                "skill_score": 9.1,
                "bio": "Lead Product Manager & Tech Career Coach. Led cross-functional teams from 0 to 1 in FinTech and EdTech.",
                "goals": "Guide engineers and designers on product sense, agile sprint management, and interview mastery.",
                "skills": ["Product Management", "Agile & Scrum", "Career Coaching", "Resume Review", "Mock Interviews"]
            }
        ]

        password = "DemoPass123!"

        created_count = 0
        for mdata in mentors_data:
            user, created = User.objects.get_or_create(
                username=mdata["username"],
                defaults={
                    "email": mdata["email"],
                    "first_name": mdata["first_name"],
                    "last_name": mdata["last_name"],
                }
            )
            if created:
                user.set_password(password)
                user.save()
                created_count += 1

            # Update Profile
            profile = user.profile
            profile.experience_level = mdata["experience_level"]
            profile.availability = mdata["availability"]
            profile.skill_score = mdata["skill_score"]
            profile.bio = mdata["bio"]
            profile.goals = mdata["goals"]
            profile.save()

            # Assign skills
            for sname in mdata["skills"]:
                if sname in all_skills:
                    profile.skills.add(all_skills[sname])

            # Ensure active Mentor role assignment
            if not user.role_assignments.filter(role="Mentor", end_time__isnull=True).exists():
                RoleAssignment.objects.create(
                    user=user,
                    role="Mentor",
                    context="Demo seed active mentor"
                )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded {len(mentors_data)} mentors ({created_count} newly created). Password: '{password}'"
        ))
