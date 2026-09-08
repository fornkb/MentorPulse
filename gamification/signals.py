from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Credit, CreditTransaction


@receiver(post_save, sender=User)
def create_user_credit(sender, instance, created, **kwargs):
    """Automatically provision 50 credits and log STARTING_BONUS transaction on user registration."""
    if created:
        credit, was_created = Credit.objects.get_or_create(user=instance, defaults={'balance': 50})
        if was_created:
            CreditTransaction.objects.create(
                user=instance,
                amount=50,
                reason='STARTING_BONUS',
                context='Welcome credit bonus upon registration'
            )
