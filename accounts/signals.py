from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, RoleAssignment


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create a Profile and initial Learner RoleAssignment when a User is created."""
    if created:
        profile, _ = Profile.objects.get_or_create(user=instance)
        # Create a default Learner role assignment if none exists yet
        if not instance.role_assignments.exists():
            RoleAssignment.objects.create(
                user=instance,
                role='Learner',
                context='Default initial role on registration'
            )


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure profile is saved when user is updated."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
