"""Transactional mentorship lifecycle and scheduling rules."""
from datetime import timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.models import F, Q
from django.utils import timezone
from django.urls import reverse
from accounts.models import Profile
from gamification.services import CreditService, BadgeService
from notifications.services import send_notification
from .models import Mentorship, Progress, Session, DiscussionPost
from mentorpulse.db import retry_database_lock


def lock_participants(mentor_id, learner_id):
    ids = sorted([mentor_id, learner_id])
    if connection.vendor == 'sqlite':
        # SQLite lacks row locks. Acquire its write lock before lifecycle reads.
        Profile.objects.filter(user_id__in=ids).update(mentor_capacity=F('mentor_capacity'))
    list(User.objects.select_for_update().filter(pk__in=ids).order_by('pk'))


@retry_database_lock
@transaction.atomic
def create_request(learner, mentor, goals, is_priority):
    lock_participants(mentor.pk, learner.pk)
    if learner.pk == mentor.pk or not learner.profile.is_learner:
        raise ValidationError('An active learner role is required to request another mentor.')
    if not mentor.is_active or not mentor.profile.is_mentor:
        raise ValidationError('This mentor is not accepting requests.')
    if Mentorship.objects.filter(mentor=mentor, learner=learner, status__in=['PENDING', 'ACTIVE']).exists():
        raise ValidationError('You already have an active mentorship or pending request with this mentor.')
    if Mentorship.objects.filter(mentor=mentor, status='ACTIVE').count() >= mentor.profile.mentor_capacity:
        raise ValidationError('This mentor is currently at capacity. Save their profile and check back later.')
    mentorship = Mentorship.objects.create(learner=learner, mentor=mentor, goals=goals, is_priority=is_priority)
    success, message = CreditService.deduct_for_request(learner, is_priority, mentorship)
    if not success:
        raise ValidationError(message)
    send_notification(mentor, f'New mentorship request from {learner.get_full_name() or learner.username}.',
        'REQUEST_RECEIVED', reverse('mentorship_list'))
    return mentorship


@retry_database_lock
@transaction.atomic
def transition_request(mentorship_id, actor, action):
    original = Mentorship.objects.get(pk=mentorship_id)
    lock_participants(original.mentor_id, original.learner_id)
    mentorship = Mentorship.objects.select_for_update().get(pk=mentorship_id)
    expected = mentorship.learner_id if action == 'CANCELLED' else mentorship.mentor_id
    if actor.pk != expected:
        raise ValidationError('Only the appropriate participant may update this request.')
    if mentorship.status != 'PENDING':
        raise ValidationError('This request has already been processed.')
    if action == 'ACTIVE':
        if not actor.profile.is_mentor or not actor.is_active:
            raise ValidationError('An active mentor role is required to accept requests.')
        if Mentorship.objects.filter(mentor=actor, status='ACTIVE').count() >= actor.profile.mentor_capacity:
            raise ValidationError('Your active mentorship capacity has been reached.')
        mentorship.start_date = timezone.localdate()
        Progress.objects.get_or_create(mentorship=mentorship)
        DiscussionPost.objects.create(mentorship=mentorship, author=actor, text=f'Welcome! Let’s work towards: {mentorship.goals}')
        send_notification(mentorship.learner, f'{actor.get_full_name() or actor.username} accepted your request.',
            'REQUEST_ACCEPTED', reverse('mentorship_workspace', args=[mentorship.pk]))
    else:
        CreditService.refund_for_request(mentorship)
        send_notification(mentorship.learner, 'Your request was cancelled or declined. Credits were refunded.',
            'REQUEST_REJECTED', reverse('mentorship_list'))
    mentorship.status = action
    mentorship.save(update_fields=['status', 'start_date'])
    return mentorship


def completion_errors(mentorship):
    errors = []
    if not mentorship.milestones.exists():
        errors.append('Add and complete at least one milestone.')
    elif mentorship.milestones.filter(is_completed=False).exists():
        errors.append('Complete every milestone before issuing a certificate.')
    sessions = mentorship.sessions.filter(is_cancelled=False)
    if not sessions.filter(is_completed=True).exists():
        errors.append('Complete at least one session.')
    if sessions.filter(is_completed=False).exists():
        errors.append('Complete or cancel all remaining sessions.')
    return errors


def certificate_snapshot(mentorship):
    return {
        'learner': mentorship.learner.get_full_name() or mentorship.learner.username,
        'mentor': mentorship.mentor.get_full_name() or mentorship.mentor.username,
        'date': str(mentorship.end_date or timezone.localdate()),
        'goals': mentorship.goals,
        'milestones': list(mentorship.milestones.filter(is_completed=True).values_list('title', flat=True)),
        'skills': list(mentorship.mentor.profile.skills.filter(
            pk__in=mentorship.learner.profile.learning_skills.values('pk')).values_list('name', flat=True)),
    }


@retry_database_lock
@transaction.atomic
def complete_mentorship(mentorship_id, actor):
    original = Mentorship.objects.get(pk=mentorship_id)
    lock_participants(original.mentor_id, original.learner_id)
    mentorship = Mentorship.objects.select_for_update().get(pk=mentorship_id)
    if actor.pk != mentorship.mentor_id:
        raise ValidationError('Only the mentor can approve completion and issue the certificate.')
    if mentorship.status != 'ACTIVE':
        raise ValidationError('Only active mentorships can be completed.')
    errors = completion_errors(mentorship)
    if errors:
        raise ValidationError(errors)
    mentorship.status = 'COMPLETED'
    mentorship.end_date = timezone.localdate()
    mentorship.certificate_id = uuid4()
    mentorship.certificate_data = certificate_snapshot(mentorship)
    mentorship.save()
    progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
    progress.recalculate()
    for user in [mentorship.mentor, mentorship.learner]:
        BadgeService.check_and_award_badges(user)
        send_notification(user, 'Mentorship completed. Your certificate is ready.', 'SESSION_LOGGED',
            reverse('mentorship_certificate', args=[mentorship.pk]))
    return mentorship


def validate_session(mentorship, date, duration_minutes, exclude_id=None):
    if mentorship.status != 'ACTIVE':
        raise ValidationError('Sessions can only be scheduled in active mentorships.')
    if date <= timezone.now():
        raise ValidationError('Choose a future date and time.')
    end = date + timedelta(minutes=duration_minutes)
    local_start = timezone.localtime(date, ZoneInfo(mentorship.mentor.profile.timezone))
    local_end = timezone.localtime(end, ZoneInfo(mentorship.mentor.profile.timezone))
    slots = mentorship.mentor.availability_slots.all()
    if slots.exists() and not any(
        local_start.date() == local_end.date() and slot.weekday == local_start.weekday()
        and slot.start_time <= local_start.time() and slot.end_time >= local_end.time() for slot in slots
    ):
        raise ValidationError('Choose a time within the mentor’s published availability.')
    ids = [mentorship.mentor_id, mentorship.learner_id]
    candidates = Session.objects.filter(is_cancelled=False, is_completed=False, mentorship__status='ACTIVE',
        date__lt=end, date__gt=date-timedelta(minutes=240)).filter(
        Q(mentorship__mentor_id__in=ids) | Q(mentorship__learner_id__in=ids)).exclude(pk=exclude_id)
    if any(s.date + timedelta(minutes=s.duration_minutes) > date for s in candidates):
        raise ValidationError('This time overlaps another session for you or your mentor.')


@retry_database_lock
@transaction.atomic
def save_session(form, mentorship, actor):
    lock_participants(mentorship.mentor_id, mentorship.learner_id)
    mentorship.refresh_from_db()
    if actor.pk not in [mentorship.mentor_id, mentorship.learner_id]:
        raise ValidationError('Only participants may schedule sessions.')
    instance = form.instance
    if instance.pk:
        current = Session.objects.select_for_update().get(pk=instance.pk)
        if current.is_completed or current.is_cancelled:
            raise ValidationError('Completed or cancelled sessions cannot be rescheduled.')
    validate_session(mentorship, form.cleaned_data['date'], form.cleaned_data['duration_minutes'], instance.pk)
    session = form.save(commit=False)
    session.mentorship = mentorship
    session.reminder_sent_at = None
    session.save()
    progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
    progress.recalculate()
    other = mentorship.learner if actor.pk == mentorship.mentor_id else mentorship.mentor
    send_notification(other, 'A mentorship session was scheduled or rescheduled. Check your workspace.',
        'SESSION_LOGGED', reverse('mentorship_workspace', args=[mentorship.pk]))
    return session
