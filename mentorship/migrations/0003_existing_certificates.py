from uuid import uuid4
from django.db import migrations


def preserve_certificates(apps, schema_editor):
    Mentorship = apps.get_model('mentorship', 'Mentorship')
    Profile = apps.get_model('accounts', 'Profile')
    for mentorship in Mentorship.objects.filter(status='COMPLETED').select_related('mentor', 'learner').iterator():
        mentor = mentorship.mentor
        learner = mentorship.learner
        mentor_profile = Profile.objects.get(user_id=mentor.pk)
        learner_profile = Profile.objects.get(user_id=learner.pk)
        mentorship.certificate_id = uuid4()
        mentorship.certificate_data = {
            'learner': f'{learner.first_name} {learner.last_name}'.strip() or learner.username,
            'mentor': f'{mentor.first_name} {mentor.last_name}'.strip() or mentor.username,
            'date': str(mentorship.end_date or mentorship.start_date), 'goals': mentorship.goals,
            'milestones': list(mentorship.milestones.filter(is_completed=True).values_list('title', flat=True)),
            'skills': list(mentor_profile.skills.filter(pk__in=learner_profile.learning_skills.values('pk')).values_list('name', flat=True)),
        }
        mentorship.save(update_fields=['certificate_id', 'certificate_data'])


class Migration(migrations.Migration):
    dependencies = [('mentorship', '0002_mentorship_certificate_data_and_more'), ('accounts', '0003_learning_goals')]
    operations = [migrations.RunPython(preserve_certificates, migrations.RunPython.noop)]
