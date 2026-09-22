from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden, JsonResponse
from .models import Mentorship, Progress, Session, Milestone, Resource, DiscussionPost
from .forms import (
    MentorshipRequestForm,
    SessionForm,
    MilestoneForm,
    ResourceForm,
    DiscussionPostForm
)
from matching.services import calculate_match_score
from gamification.services import CreditService, FeedbackService, BadgeService, LeaderboardService
from gamification.forms import FeedbackForm


@login_required
def request_mentorship_view(request, mentor_id):
    """Initiate a mentorship request to a mentor with goals and optional priority flag."""
    mentor = get_object_or_404(User.objects.select_related('profile'), id=mentor_id)

    # 1. Validation: Cannot request self
    if request.user == mentor:
        messages.error(request, "You cannot send a mentorship request to yourself.")
        return redirect('mentor_detail', user_id=mentor_id)

    # 2. Validation: Target user must be an active mentor
    if not mentor.role_assignments.filter(role='Mentor', end_time__isnull=True).exists():
        messages.error(request, f"{mentor.username} is not currently accepting mentorship requests.")
        return redirect('mentor_list')

    # 3. Check for existing active or pending mentorship
    existing = Mentorship.objects.filter(
        learner=request.user,
        mentor=mentor,
        status__in=['PENDING', 'ACTIVE']
    ).first()

    if existing:
        if existing.status == 'ACTIVE':
            messages.info(request, f"You already have an active mentorship with {mentor.get_full_name() or mentor.username}.")
            return redirect('mentorship_workspace', mentorship_id=existing.id)
        else:
            messages.warning(request, f"You already have a pending request awaiting review from {mentor.get_full_name() or mentor.username}.")
            return redirect('mentorship_list')

    # Calculate match breakdown for context
    match_data = calculate_match_score(request.user.profile, mentor.profile)

    if request.method == 'POST':
        form = MentorshipRequestForm(request.POST)
        if form.is_valid():
            is_priority = form.cleaned_data.get('is_priority', False)
            success, msg = CreditService.deduct_for_request(request.user, is_priority=is_priority)
            if not success:
                messages.error(request, msg)
                return render(request, 'mentorship/request_mentorship.html', {
                    'mentor': mentor,
                    'profile': mentor.profile,
                    'form': form,
                    'match_data': match_data,
                })

            mentorship = form.save(commit=False)
            mentorship.learner = request.user
            mentorship.mentor = mentor
            mentorship.status = 'PENDING'
            mentorship.save()

            messages.success(
                request,
                f"Your mentorship request has been submitted to {mentor.get_full_name() or mentor.username}! "
                f"{'⭐ Priority flag activated.' if mentorship.is_priority else ''} "
                f"({15 if is_priority else 10} credits deducted from your wallet)."
            )
            return redirect('mentorship_list')
    else:
        form = MentorshipRequestForm()

    context = {
        'mentor': mentor,
        'profile': mentor.profile,
        'form': form,
        'match_data': match_data,
    }
    return render(request, 'mentorship/request_mentorship.html', context)



@login_required
def mentorship_list_view(request):
    """Central hub for all user mentorships (Active, Pending Incoming, Pending Outgoing, Completed)."""
    user = request.user

    # 1. Active Mentorships (both as Learner and as Mentor)
    active_mentorships = Mentorship.objects.filter(
        status='ACTIVE'
    ).filter(
        learner=user
    ) | Mentorship.objects.filter(
        status='ACTIVE',
        mentor=user
    )
    active_mentorships = active_mentorships.select_related('mentor__profile', 'learner__profile', 'progress').distinct()

    # 2. Incoming Pending Requests (for mentors)
    incoming_requests = Mentorship.objects.filter(
        mentor=user,
        status='PENDING'
    ).select_related('learner__profile').order_by('-is_priority', '-id')

    # 3. Outgoing Pending Requests (for learners)
    outgoing_requests = Mentorship.objects.filter(
        learner=user,
        status='PENDING'
    ).select_related('mentor__profile').order_by('-id')

    # 4. Completed Mentorships
    completed_mentorships = Mentorship.objects.filter(
        status='COMPLETED'
    ).filter(
        learner=user
    ) | Mentorship.objects.filter(
        status='COMPLETED',
        mentor=user
    )
    completed_mentorships = completed_mentorships.select_related('mentor__profile', 'learner__profile', 'progress').distinct()

    context = {
        'active_mentorships': active_mentorships,
        'incoming_requests': incoming_requests,
        'outgoing_requests': outgoing_requests,
        'completed_mentorships': completed_mentorships,
        'has_pending_incoming': incoming_requests.exists(),
        'total_active_count': active_mentorships.count(),
    }
    return render(request, 'mentorship/mentorship_list.html', context)


@login_required
def accept_mentorship_view(request, mentorship_id):
    """Accept an incoming pending mentorship request (Mentor only)."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id, mentor=request.user)

    if mentorship.status == 'PENDING':
        mentorship.status = 'ACTIVE'
        mentorship.start_date = timezone.now().date()
        mentorship.save()

        # Initialize progress tracker
        progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
        progress.recalculate()

        # Create default welcome discussion post
        DiscussionPost.objects.create(
            mentorship=mentorship,
            author=request.user,
            text=f"Welcome to our mentorship! I have accepted your request and look forward to collaborating towards your goals: '{mentorship.goals}'."
        )

        messages.success(request, f"Mentorship with {mentorship.learner.get_full_name() or mentorship.learner.username} is now ACTIVE! Welcome to the workspace.")
        return redirect('mentorship_workspace', mentorship_id=mentorship.id)

    messages.warning(request, f"Mentorship request is already {mentorship.status.lower()}.")
    return redirect('mentorship_list')


@login_required
def reject_mentorship_view(request, mentorship_id):
    """Decline an incoming pending mentorship request (Mentor only)."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id, mentor=request.user)

    if mentorship.status == 'PENDING':
        mentorship.status = 'REJECTED'
        mentorship.save()
        CreditService.refund_for_request(mentorship)
        messages.info(request, f"Mentorship request from {mentorship.learner.username} was declined and credits were refunded.")

    return redirect('mentorship_list')


@login_required
def cancel_mentorship_view(request, mentorship_id):
    """Cancel an outgoing pending mentorship request (Learner only)."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id, learner=request.user)

    if mentorship.status == 'PENDING':
        mentorship.status = 'CANCELLED'
        mentorship.save()
        CreditService.refund_for_request(mentorship)
        messages.info(request, "Your mentorship request was cancelled and your credits were refunded.")

    return redirect('mentorship_list')


@login_required
def mentorship_workspace_view(request, mentorship_id):
    """Collaborative Mentorship Hub for participants (Sessions, Milestones, Resources, Discussions)."""
    mentorship = get_object_or_404(
        Mentorship.objects.select_related('mentor__profile', 'learner__profile', 'progress'),
        id=mentorship_id
    )

    # Permission check
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden("You are not an authorized participant in this mentorship.")

    # Ensure progress record exists
    progress, _ = Progress.objects.get_or_create(mentorship=mentorship)
    progress.recalculate()

    # Forms for modals / tabs
    session_form = SessionForm()
    milestone_form = MilestoneForm()
    resource_form = ResourceForm()
    discussion_form = DiscussionPostForm()
    feedback_form = FeedbackForm()

    # Content
    sessions = mentorship.sessions.all().order_by('date')
    milestones = mentorship.milestones.all().order_by('id')
    resources = mentorship.resources.all().order_by('-created_at')
    discussion_posts = mentorship.discussion_posts.all().select_related('author').order_by('created_at')
    feedbacks = mentorship.feedbacks.all().select_related('given_by', 'given_to').order_by('-created_at')
    has_given_feedback = mentorship.feedbacks.filter(given_by=request.user).exists()

    # Completed metrics
    completed_milestones = milestones.filter(is_completed=True).count()
    completed_sessions = sessions.filter(is_completed=True).count()

    context = {
        'mentorship': mentorship,
        'progress': progress,
        'sessions': sessions,
        'milestones': milestones,
        'resources': resources,
        'discussion_posts': discussion_posts,
        'feedbacks': feedbacks,
        'has_given_feedback': has_given_feedback,
        'completed_milestones': completed_milestones,
        'completed_sessions': completed_sessions,
        'session_form': session_form,
        'milestone_form': milestone_form,
        'resource_form': resource_form,
        'discussion_form': discussion_form,
        'feedback_form': feedback_form,
        'is_mentor': request.user == mentorship.mentor,
        'is_learner': request.user == mentorship.learner,
    }
    return render(request, 'mentorship/workspace.html', context)


@login_required
def session_add_view(request, mentorship_id):
    """Schedule a new mentorship session."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = SessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.mentorship = mentorship
            session.save()
            mentorship.progress.recalculate()
            messages.success(request, f"New session scheduled for {session.date.strftime('%b %d, %Y at %I:%M %p')}.")
        else:
            messages.error(request, "Failed to schedule session. Please verify date format.")

    return redirect('mentorship_workspace', mentorship_id=mentorship.id)


@login_required
def session_toggle_view(request, session_id):
    """Toggle a session's completion status."""
    session = get_object_or_404(Session, id=session_id)
    if not session.mentorship.can_access(request.user):
        return HttpResponseForbidden()

    session.is_completed = not session.is_completed
    session.save()
    session.mentorship.progress.recalculate()

    if session.is_completed:
        CreditService.reward_mentor_for_session(session)
        messages.success(request, "Session marked as completed! Mentor awarded +10 credits.")
    else:
        messages.success(request, "Session marked as incomplete.")
    return redirect('mentorship_workspace', mentorship_id=session.mentorship.id)


@login_required
def milestone_add_view(request, mentorship_id):
    """Add a new milestone to the mentorship checklist."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.mentorship = mentorship
            milestone.save()
            mentorship.progress.recalculate()
            messages.success(request, f"Added milestone: '{milestone.title}'")

    return redirect('mentorship_workspace', mentorship_id=mentorship.id)


@login_required
def milestone_toggle_view(request, milestone_id):
    """Toggle completion status of a milestone."""
    milestone = get_object_or_404(Milestone, id=milestone_id)
    if not milestone.mentorship.can_access(request.user):
        return HttpResponseForbidden()

    milestone.is_completed = not milestone.is_completed
    milestone.completed_at = timezone.now() if milestone.is_completed else None
    milestone.save()
    pct = milestone.mentorship.progress.recalculate()

    messages.success(request, f"Milestone updated! Progress is now {pct}%.")
    return redirect('mentorship_workspace', mentorship_id=milestone.mentorship.id)


@login_required
def resource_add_view(request, mentorship_id):
    """Upload or share a link/file/note in the workspace."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.mentorship = mentorship
            resource.uploaded_by = request.user
            resource.save()
            BadgeService.check_and_award_badges(request.user)
            LeaderboardService.recalculate_leaderboard()
            messages.success(request, f"Shared resource: '{resource.title}' ({resource.type}).")
        else:
            for field, errs in form.errors.items():
                for e in errs:
                    messages.error(request, f"{field.capitalize()}: {e}")

    return redirect('mentorship_workspace', mentorship_id=mentorship.id)


@login_required
def discussion_post_view(request, mentorship_id):
    """Post an asynchronous message to the mentorship pair."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        form = DiscussionPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.mentorship = mentorship
            post.author = request.user
            post.save()
            messages.success(request, "Message posted to discussion thread.")

    return redirect('mentorship_workspace', mentorship_id=mentorship.id)


@login_required
def mentorship_complete_view(request, mentorship_id):
    """Finalize and complete an active mentorship."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()

    if mentorship.status == 'ACTIVE':
        mentorship.status = 'COMPLETED'
        mentorship.end_date = timezone.now().date()
        mentorship.save()
        mentorship.progress.recalculate()

        # Check badges for both parties & refresh leaderboard
        BadgeService.check_and_award_badges(mentorship.mentor)
        BadgeService.check_and_award_badges(mentorship.learner)
        LeaderboardService.recalculate_leaderboard()

        messages.success(request, "Congratulations! This mentorship has been marked as COMPLETED. Your certificate is now unlocked!")
        return redirect('mentorship_certificate', mentorship_id=mentorship.id)

    return redirect('mentorship_workspace', mentorship_id=mentorship.id)


@login_required
def certificate_view(request, mentorship_id):
    """Print-friendly completion certificate for completed mentorships."""
    mentorship = get_object_or_404(
        Mentorship.objects.select_related('mentor__profile', 'learner__profile'),
        id=mentorship_id
    )

    if not mentorship.can_access(request.user):
        return HttpResponseForbidden("You do not have permission to view this certificate.")

    if mentorship.status != 'COMPLETED':
        messages.warning(request, "Certificates are only issued for COMPLETED mentorships.")
        return redirect('mentorship_workspace', mentorship_id=mentorship.id)

    completed_milestones = mentorship.milestones.filter(is_completed=True)
    shared_skills = set(mentorship.learner.profile.skills.all()) & set(mentorship.mentor.profile.skills.all())

    context = {
        'mentorship': mentorship,
        'learner': mentorship.learner,
        'mentor': mentorship.mentor,
        'completed_milestones': completed_milestones,
        'shared_skills': shared_skills,
        'completion_date': mentorship.end_date or timezone.now().date(),
    }
    return render(request, 'mentorship/certificate.html', context)
