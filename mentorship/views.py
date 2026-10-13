from datetime import timedelta, timezone as datetime_timezone
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden, HttpResponse, FileResponse
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Mentorship, Progress, Session, Milestone, Resource, DiscussionPost
from .forms import MentorshipRequestForm, SessionForm, MilestoneForm, ResourceForm, DiscussionPostForm
from .services import create_request, transition_request, completion_errors, complete_mentorship, save_session, lock_participants
from matching.services import calculate_match_score
from gamification.services import CreditService, BadgeService
from gamification.forms import FeedbackForm
from notifications.services import send_notification
from mentorpulse.db import retry_database_lock


def show_errors(request, error):
    for message in error.messages:
        messages.error(request, message)


def workspace_redirect(mentorship):
    return redirect('mentorship_workspace', mentorship_id=mentorship.pk)


@login_required
def request_mentorship_view(request, mentor_id):
    mentor = get_object_or_404(User.objects.select_related('profile'), pk=mentor_id, is_active=True)
    if request.user == mentor or not mentor.profile.is_mentor:
        messages.error(request, 'Choose another active mentor.')
        return redirect('mentor_list')
    existing = Mentorship.objects.filter(learner=request.user, mentor=mentor, status__in=['PENDING', 'ACTIVE']).first()
    if existing:
        messages.info(request, 'You already have an open request or mentorship with this mentor.')
        return workspace_redirect(existing) if existing.status == 'ACTIVE' else redirect('mentorship_list')
    form = MentorshipRequestForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            create_request(request.user, mentor, form.cleaned_data['goals'], form.cleaned_data['is_priority'])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Request submitted. Your wallet was charged once.')
            return redirect('mentorship_list')
    return render(request, 'mentorship/request_mentorship.html', {
        'mentor': mentor, 'profile': mentor.profile, 'form': form,
        'match_data': calculate_match_score(request.user.profile, mentor.profile),
    })


@login_required
def mentorship_list_view(request):
    user = request.user
    involved = Mentorship.objects.filter(Q(mentor=user) | Q(learner=user)).select_related('mentor__profile', 'learner__profile', 'progress')
    active = involved.filter(status='ACTIVE')
    incoming = involved.filter(mentor=user, status='PENDING')
    return render(request, 'mentorship/mentorship_list.html', {
        'active_mentorships': active, 'incoming_requests': incoming,
        'outgoing_requests': involved.filter(learner=user, status='PENDING'),
        'completed_mentorships': involved.filter(status='COMPLETED'),
        'has_pending_incoming': incoming.exists(), 'total_active_count': active.count(),
    })


def process_request(request, mentorship_id, action):
    mentorship = get_object_or_404(Mentorship, pk=mentorship_id)
    owner_id = mentorship.learner_id if action == 'CANCELLED' else mentorship.mentor_id
    if owner_id != request.user.pk:
        return HttpResponseForbidden('Only the appropriate participant can process this request.')
    try:
        mentorship = transition_request(mentorship_id, request.user, action)
    except ValidationError as error:
        show_errors(request, error)
    else:
        messages.success(request, 'Request accepted.' if action == 'ACTIVE' else 'Request closed and credits refunded.')
        if action == 'ACTIVE':
            return workspace_redirect(mentorship)
    return redirect('mentorship_list')


@login_required
@require_POST
def accept_mentorship_view(request, mentorship_id):
    return process_request(request, mentorship_id, 'ACTIVE')


@login_required
@require_POST
def reject_mentorship_view(request, mentorship_id):
    return process_request(request, mentorship_id, 'REJECTED')


@login_required
@require_POST
def cancel_mentorship_view(request, mentorship_id):
    return process_request(request, mentorship_id, 'CANCELLED')


@login_required
def mentorship_workspace_view(request, mentorship_id):
    mentorship = get_object_or_404(Mentorship.objects.select_related('mentor__profile', 'learner__profile', 'progress'), pk=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden('This workspace is private to its participants.')
    progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
    sessions = mentorship.sessions.all().order_by('date')
    milestones = mentorship.milestones.all().order_by('id')
    return render(request, 'mentorship/workspace.html', {
        'mentorship': mentorship, 'progress': progress,
        'sessions': sessions, 'milestones': milestones,
        'resources': mentorship.resources.select_related('uploaded_by').all(),
        'discussion_posts': mentorship.discussion_posts.select_related('author').all(),
        'feedbacks': mentorship.feedbacks.select_related('given_by', 'given_to').all(),
        'has_given_feedback': mentorship.feedbacks.filter(given_by=request.user).exists(),
        'completed_milestones': milestones.filter(is_completed=True).count(),
        'completed_sessions': sessions.filter(is_completed=True, is_cancelled=False).count(),
        'session_form': SessionForm(auto_id='session_%s'), 'milestone_form': MilestoneForm(auto_id='milestone_%s'),
        'resource_form': ResourceForm(auto_id='resource_%s'), 'discussion_form': DiscussionPostForm(auto_id='discussion_%s'), 'feedback_form': FeedbackForm(),
        'is_mentor': request.user.pk == mentorship.mentor_id,
        'is_learner': request.user.pk == mentorship.learner_id,
        'can_review': request.user.pk in [mentorship.mentor_id, mentorship.learner_id] and mentorship.status in ['ACTIVE', 'COMPLETED'],
        'editable': mentorship.status == 'ACTIVE' and request.user.pk in [mentorship.mentor_id, mentorship.learner_id],
        'completion_errors': completion_errors(mentorship) if mentorship.status == 'ACTIVE' else [],
    })


def edit_form_response(request, mentorship, form, title):
    return render(request, 'mentorship/edit_item.html', {'form': form, 'title': title, 'mentorship': mentorship,
        'mentor_slots': mentorship.mentor.availability_slots.all()})


@login_required
def session_add_view(request, mentorship_id):
    return session_editor(request, get_object_or_404(Mentorship, pk=mentorship_id))


@login_required
def session_edit_view(request, session_id):
    session = get_object_or_404(Session.objects.select_related('mentorship'), pk=session_id)
    return session_editor(request, session.mentorship, session)


def session_editor(request, mentorship, session=None):
    if request.user.pk not in [mentorship.mentor_id, mentorship.learner_id] or mentorship.status != 'ACTIVE':
        return HttpResponseForbidden('Sessions can only be changed by participants in an active mentorship.')
    if session and (session.is_completed or session.is_cancelled):
        return HttpResponseForbidden('Completed or cancelled sessions cannot be edited.')
    form = SessionForm(request.POST if request.method == 'POST' else None, instance=session)
    if request.method == 'POST' and form.is_valid():
        try:
            save_session(form, mentorship, request.user)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            messages.success(request, 'Session saved. Times are shown in your profile time zone.')
            return workspace_redirect(mentorship)
    return edit_form_response(request, mentorship, form, 'Reschedule session' if session else 'Schedule session')


@login_required
@require_POST
@retry_database_lock
@transaction.atomic
def session_toggle_view(request, session_id):
    original = get_object_or_404(Session, pk=session_id)
    lock_participants(original.mentorship.mentor_id, original.mentorship.learner_id)
    session = Session.objects.select_for_update().select_related('mentorship').get(pk=session_id)
    if request.user.pk != session.mentorship.mentor_id or session.mentorship.status != 'ACTIVE':
        return HttpResponseForbidden('Only the mentor can confirm completed sessions in an active mentorship.')
    if session.is_cancelled or session.date + timedelta(minutes=session.duration_minutes) > timezone.now():
        messages.error(request, 'Only sessions that have ended and are not cancelled can be completed.')
        return workspace_redirect(session.mentorship)
    if not session.is_completed:
        session.is_completed = True
        session.save(update_fields=['is_completed'])
        awarded = CreditService.reward_mentor_for_session(session)
        messages.success(request, 'Session completed.' + (' Mentor earned 10 credits.' if awarded else ''))
        send_notification(session.mentorship.learner, 'Your mentor confirmed the session as completed.',
            'SESSION_LOGGED', reverse('mentorship_workspace', args=[session.mentorship_id]))
    progress, _ = Progress.objects.get_or_create(mentorship=session.mentorship)
    progress.recalculate()
    return workspace_redirect(session.mentorship)


@login_required
@require_POST
@retry_database_lock
@transaction.atomic
def session_cancel_view(request, session_id):
    original = get_object_or_404(Session, pk=session_id)
    lock_participants(original.mentorship.mentor_id, original.mentorship.learner_id)
    session = Session.objects.select_for_update().select_related('mentorship').get(pk=session_id)
    mentorship = session.mentorship
    if request.user.pk not in [mentorship.mentor_id, mentorship.learner_id] or mentorship.status != 'ACTIVE':
        return HttpResponseForbidden()
    if session.is_completed:
        messages.error(request, 'Completed sessions cannot be cancelled.')
    elif not session.is_cancelled:
        session.is_cancelled = True
        session.save(update_fields=['is_cancelled'])
        other = mentorship.learner if request.user.pk == mentorship.mentor_id else mentorship.mentor
        send_notification(other, 'A scheduled session was cancelled.', 'SESSION_LOGGED', reverse('mentorship_workspace', args=[mentorship.pk]))
        progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
        progress.recalculate()
        messages.success(request, 'Session cancelled. It no longer blocks scheduling or completion.')
    return workspace_redirect(mentorship)


@login_required
def milestone_add_view(request, mentorship_id):
    return milestone_editor(request, get_object_or_404(Mentorship, pk=mentorship_id))


@login_required
def milestone_edit_view(request, milestone_id):
    milestone = get_object_or_404(Milestone.objects.select_related('mentorship'), pk=milestone_id)
    return milestone_editor(request, milestone.mentorship, milestone)


def milestone_editor(request, mentorship, milestone=None):
    if request.user.pk not in [mentorship.mentor_id, mentorship.learner_id] or mentorship.status != 'ACTIVE':
        return HttpResponseForbidden('Milestones can only be changed in active mentorships.')
    form = MilestoneForm(request.POST if request.method == 'POST' else None, instance=milestone)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            lock_participants(mentorship.mentor_id, mentorship.learner_id)
            mentorship.refresh_from_db()
            if mentorship.status != 'ACTIVE':
                return HttpResponseForbidden('This mentorship is no longer active.')
            item = form.save(commit=False)
            item.mentorship = mentorship
            item.save()
            progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
            progress.recalculate()
        messages.success(request, 'Milestone saved.')
        return workspace_redirect(mentorship)
    return edit_form_response(request, mentorship, form, 'Edit milestone' if milestone else 'Add milestone')


@login_required
@require_POST
@retry_database_lock
@transaction.atomic
def milestone_toggle_view(request, milestone_id):
    original = get_object_or_404(Milestone, pk=milestone_id)
    lock_participants(original.mentorship.mentor_id, original.mentorship.learner_id)
    item = Milestone.objects.select_for_update().select_related('mentorship').get(pk=milestone_id)
    if request.user.pk not in [item.mentorship.mentor_id, item.mentorship.learner_id] or item.mentorship.status != 'ACTIVE':
        return HttpResponseForbidden()
    item.is_completed = not item.is_completed
    item.completed_at = timezone.now() if item.is_completed else None
    item.save()
    progress, _ = Progress.objects.get_or_create(mentorship=item.mentorship)
    progress.recalculate()
    return workspace_redirect(item.mentorship)


@login_required
def resource_add_view(request, mentorship_id):
    return add_workspace_item(request, mentorship_id, ResourceForm, 'Share resource', 'resource')


@login_required
def discussion_post_view(request, mentorship_id):
    return add_workspace_item(request, mentorship_id, DiscussionPostForm, 'Post a discussion message', 'discussion')


def add_workspace_item(request, mentorship_id, form_class, title, kind):
    mentorship = get_object_or_404(Mentorship, pk=mentorship_id)
    if request.user.pk not in [mentorship.mentor_id, mentorship.learner_id] or mentorship.status != 'ACTIVE':
        return HttpResponseForbidden('This workspace is read-only.')
    form = form_class(request.POST if request.method == 'POST' else None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            lock_participants(mentorship.mentor_id, mentorship.learner_id)
            mentorship.refresh_from_db()
            if mentorship.status != 'ACTIVE':
                return HttpResponseForbidden('This workspace is read-only.')
            item = form.save(commit=False)
            item.mentorship = mentorship
            if kind == 'resource':
                item.uploaded_by = request.user
            else:
                item.author = request.user
            item.save()
            if kind == 'resource':
                BadgeService.check_and_award_badges(request.user)
            else:
                other = mentorship.learner if request.user.pk == mentorship.mentor_id else mentorship.mentor
                send_notification(other, f'{request.user.get_full_name() or request.user.username} posted a discussion message.',
                    'DISCUSSION', reverse('mentorship_workspace', args=[mentorship.pk]))
        messages.success(request, 'Resource shared.' if kind == 'resource' else 'Message posted.')
        return workspace_redirect(mentorship)
    return edit_form_response(request, mentorship, form, title)


@login_required
@require_POST
def mentorship_complete_view(request, mentorship_id):
    mentorship = get_object_or_404(Mentorship, pk=mentorship_id)
    if request.user.pk != mentorship.mentor_id:
        return HttpResponseForbidden('Only the mentor can issue a certificate.')
    try:
        complete_mentorship(mentorship_id, request.user)
    except ValidationError as error:
        show_errors(request, error)
        return workspace_redirect(mentorship)
    messages.success(request, 'Mentorship completed and certificate issued.')
    return redirect('mentorship_certificate', mentorship_id=mentorship.pk)


@login_required
def resource_download_view(request, resource_id):
    resource = get_object_or_404(Resource.objects.select_related('mentorship'), pk=resource_id, type='FILE')
    if not resource.mentorship.can_access(request.user):
        return HttpResponseForbidden()
    if not resource.file:
        return HttpResponse(status=404)
    try:
        return FileResponse(resource.file.open('rb'), as_attachment=True, filename=resource.file.name.rsplit('/', 1)[-1])
    except FileNotFoundError:
        return HttpResponse('This file is unavailable.', status=404)


def ics_escape(value):
    return value.replace('\\', '\\\\').replace('\n', '\\n').replace(';', '\\;').replace(',', '\\,').replace('\r', '')


@login_required
def session_calendar_view(request, session_id):
    session = get_object_or_404(Session.objects.select_related('mentorship'), pk=session_id)
    if not session.mentorship.can_access(request.user):
        return HttpResponseForbidden()
    def stamp(date):
        return date.astimezone(datetime_timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//MentorPulse//Sessions//EN', 'METHOD:PUBLISH',
        'BEGIN:VEVENT', f'UID:session-{session.pk}@mentorpulse', f'DTSTAMP:{stamp(timezone.now())}',
        f'DTSTART:{stamp(session.date)}', f'DTEND:{stamp(session.date + timedelta(minutes=session.duration_minutes))}',
        f'SUMMARY:{ics_escape("MentorPulse mentorship session")}',
        f'DESCRIPTION:{ics_escape(session.notes)}', f'LOCATION:{ics_escape(session.meeting_link)}',
        'STATUS:CANCELLED' if session.is_cancelled else 'STATUS:CONFIRMED', 'END:VEVENT', 'END:VCALENDAR']
    # Fold at UTF-8 byte boundaries, as required by the iCalendar format.
    folded = []
    for line in lines:
        part = ''
        for char in line:
            if len((part + char).encode('utf-8')) > 75:
                folded.append(part)
                part = ' '
            part += char
        folded.append(part)
    response = HttpResponse('\r\n'.join(folded) + '\r\n', content_type='text/calendar; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="mentorpulse-session-{session.pk}.ics"'
    return response


def certificate_context(mentorship):
    return {'mentorship': mentorship, 'credential': mentorship.certificate_data,
            'learner': mentorship.learner, 'mentor': mentorship.mentor,
            'completed_milestones': mentorship.milestones.filter(is_completed=True),
            'shared_skills': mentorship.certificate_data.get('skills', []),
            'completion_date': mentorship.end_date}


@login_required
def certificate_view(request, mentorship_id):
    mentorship = get_object_or_404(Mentorship.objects.select_related('mentor', 'learner'), pk=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()
    if mentorship.status != 'COMPLETED' or not mentorship.certificate_id:
        messages.warning(request, 'A certificate is available once the mentor approves completion.')
        return workspace_redirect(mentorship)
    return render(request, 'mentorship/certificate.html', certificate_context(mentorship))


def certificate_verify_view(request, certificate_id):
    mentorship = get_object_or_404(Mentorship, certificate_id=certificate_id, status='COMPLETED')
    return render(request, 'mentorship/verify_certificate.html', certificate_context(mentorship))


@login_required
def certificate_pdf_view(request, mentorship_id):
    from html import escape
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    mentorship = get_object_or_404(Mentorship, pk=mentorship_id, status='COMPLETED', certificate_id__isnull=False)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()
    credential = mentorship.certificate_data
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=landscape(A4), title='MentorPulse Certificate of Completion',
        rightMargin=64, leftMargin=64, topMargin=55, bottomMargin=45)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CertificateTitle', fontName='Helvetica-Bold', fontSize=26, leading=32, alignment=1, textColor=colors.HexColor('#4338ca')))
    styles.add(ParagraphStyle(name='CertificateBody', fontSize=13, leading=20, alignment=1, spaceAfter=12))
    styles.add(ParagraphStyle(name='CertificateSmall', fontSize=9, leading=13, alignment=1))
    verification = request.build_absolute_uri(reverse('certificate_verify', args=[mentorship.certificate_id]))
    story = [Paragraph('MENTORPULSE', styles['CertificateSmall']), Spacer(1, 18),
        Paragraph('Certificate of Completion', styles['CertificateTitle']), Spacer(1, 24),
        Paragraph('Awarded to', styles['CertificateBody']),
        Paragraph(escape(credential.get('learner', '')), styles['CertificateTitle']), Spacer(1, 18),
        Paragraph('For completing a mentorship guided by ' + escape(credential.get('mentor', '')), styles['CertificateBody']),
        Paragraph('Completed on ' + escape(credential.get('date', '')), styles['CertificateBody']),
        Paragraph('Skills: ' + escape(', '.join(credential.get('skills', [])) or 'Personal learning roadmap'), styles['CertificateBody']),
        Spacer(1, 20), Paragraph('Certificate ID: ' + str(mentorship.certificate_id), styles['CertificateSmall']),
        Paragraph('Verify: ' + escape(verification), styles['CertificateSmall'])]
    doc.build(story)
    output.seek(0)
    return FileResponse(output, as_attachment=True, filename=f'mentorpulse-certificate-{mentorship.certificate_id}.pdf')
