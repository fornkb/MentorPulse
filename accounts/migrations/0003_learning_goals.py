from django.db import migrations


def preserve_learning_goals(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    RoleAssignment = apps.get_model('accounts', 'RoleAssignment')
    learner_ids = RoleAssignment.objects.filter(role='Learner', end_time__isnull=True).values_list('user_id', flat=True)
    for profile in Profile.objects.filter(user_id__in=learner_ids).iterator():
        profile.learning_skills.set(profile.skills.all())


class Migration(migrations.Migration):
    dependencies = [('accounts', '0002_profile_email_verified_profile_learning_skills_and_more')]
    operations = [migrations.RunPython(preserve_learning_goals, migrations.RunPython.noop)]
