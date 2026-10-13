from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.core.exceptions import ValidationError
from django.core import signing
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from django.conf import settings
from .models import Profile, Skill, RoleAssignment, AvailabilitySlot, SavedMentor
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserUpdateForm,
    ProfileEditForm,
    RoleToggleForm, AvailabilitySlotForm, UserReportForm
)


def register_view(request):
    """Handle new user registration with initial role assignment."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(user)
            # Log the user in immediately after registration
            login(request, user)
            messages.success(request, f"Welcome to MentorPulse, {user.first_name or user.username}! Your profile has been created.")
            return redirect('profile_edit')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """Custom authentication view with friendly demo presets and error handling."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    next_url = request.GET.get('next', 'dashboard')
    if next_url != 'dashboard' and not url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        next_url = 'dashboard'

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', True)

            user = authenticate(request, username=username, password=password)
            if user is not None:
                if not user.is_active:
                    messages.error(request, "This account is currently disabled.")
                    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})

                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                else:
                    request.session.set_expiry(1209600)  # 2 weeks

                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                return redirect(next_url if next_url and next_url != 'login' else 'dashboard')
            else:
                messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """Log the user out and redirect to login."""
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect('login')


@login_required
def dashboard_view(request):
    """Role-aware landing dashboard for authenticated users."""
    profile = request.user.profile
    skills = profile.skills.all()
    
    # Categorize skills for clean presentation
    skills_by_category = {}
    for skill in skills:
        skills_by_category.setdefault(skill.category, []).append(skill)

    role_history = request.user.role_assignments.all()[:5]

    context = {
        'profile': profile,
        'skills': skills,
        'skills_by_category': skills_by_category,
        'is_mentor': profile.is_mentor,
        'is_learner': profile.is_learner,
        'active_roles': profile.active_roles,
        'role_history': role_history,
    }
    from mentorship.models import Mentorship, Session, Milestone
    from gamification.services import CreditService
    involved = Mentorship.objects.filter(Q(mentor=request.user) | Q(learner=request.user))
    active = involved.filter(status='ACTIVE').select_related('mentor', 'learner', 'progress')
    context.update({
        'active_mentorships': active[:5], 'active_count': active.count(),
        'pending_incoming_count': involved.filter(mentor=request.user, status='PENDING').count(),
        'pending_outgoing_count': involved.filter(learner=request.user, status='PENDING').count(),
        'upcoming_sessions': Session.objects.filter(mentorship__in=active, is_completed=False,
            is_cancelled=False, date__gte=timezone.now()).select_related('mentorship__mentor', 'mentorship__learner').order_by('date')[:5],
        'next_tasks': Milestone.objects.filter(mentorship__in=active, is_completed=False)
            .select_related('mentorship').order_by('due_date', 'id')[:5],
        'wallet': CreditService.get_or_create_credit(request.user),
    })
    return render(request, 'accounts/dashboard.html', context)


@login_required
def profile_view(request, username=None):
    """View personal or another user's profile."""
    if username:
        target_user = get_object_or_404(User, username=username)
    else:
        target_user = request.user

    profile = target_user.profile
    skills = profile.skills.all()
    skills_by_category = {}
    for skill in skills:
        skills_by_category.setdefault(skill.category, []).append(skill)

    context = {
        'target_user': target_user,
        'profile': profile,
        'skills': skills,
        'skills_by_category': skills_by_category,
        'is_mentor': profile.is_mentor,
        'is_learner': profile.is_learner,
        'is_own_profile': target_user == request.user,
    }
    context['learning_skills'] = profile.learning_skills.all()
    return render(request, 'accounts/profile_detail.html', context)


@login_required
@transaction.atomic
def profile_edit_view(request):
    """Edit user details, skills, bio, availability, and active roles."""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=profile)
        role_form = RoleToggleForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid() and role_form.is_valid():
            # ModelForm validation mutates its instance; load the persisted email.
            old_email = User.objects.values_list('email', flat=True).get(pk=user.pk)
            user_form.save()
            profile_form.save()
            if old_email.lower() != user.email.lower():
                profile.email_verified = False
                profile.save(update_fields=['email_verified'])
                send_verification_email(user)

            # Handle role updates
            is_mentor = role_form.cleaned_data['is_mentor']
            is_learner = role_form.cleaned_data['is_learner']

            # Mentor role
            mentor_assignment = user.role_assignments.filter(role='Mentor', end_time__isnull=True).first()
            if is_mentor and not mentor_assignment:
                RoleAssignment.objects.create(user=user, role='Mentor', context='Activated in profile settings')
            elif not is_mentor and mentor_assignment:
                user.role_assignments.filter(role='Mentor', end_time__isnull=True).update(end_time=timezone.now())

            # Learner role
            learner_assignment = user.role_assignments.filter(role='Learner', end_time__isnull=True).first()
            if is_learner and not learner_assignment:
                RoleAssignment.objects.create(user=user, role='Learner', context='Activated in profile settings')
            elif not is_learner and learner_assignment:
                user.role_assignments.filter(role='Learner', end_time__isnull=True).update(end_time=timezone.now())

            messages.success(request, "Your profile and roles have been updated successfully!")
            return redirect('dashboard')
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = ProfileEditForm(instance=profile)
        role_form = RoleToggleForm(initial={
            'is_mentor': profile.is_mentor,
            'is_learner': profile.is_learner,
        })

    # Group all available skills by category for rich checkbox selection
    all_skills = Skill.objects.all().order_by('category', 'name')
    skills_by_category = {}
    for skill in all_skills:
        skills_by_category.setdefault(skill.category, []).append(skill)

    current_skill_ids = set(profile_form['skills'].value() or []) if profile_form.is_bound else set(profile.skills.values_list('id', flat=True))
    current_skill_ids = {int(pk) for pk in current_skill_ids if str(pk).isdecimal()}

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'role_form': role_form,
        'skills_by_category': skills_by_category,
        'current_skill_ids': current_skill_ids,
    }
    return render(request, 'accounts/profile_edit.html', context)


def switch_user_view(request, user_id):
    """Instant demo role & user switcher for live evaluations (DEBUG mode only)."""
    if not settings.DEBUG:
        return HttpResponseForbidden("Demo user switching is disabled outside DEBUG mode.")

    target_user = get_object_or_404(User, id=user_id)
    login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')

    role_label = "User"
    if target_user.is_superuser or target_user.is_staff:
        role_label = "Admin / Superuser"
    elif hasattr(target_user, 'profile'):
        roles = target_user.profile.active_roles
        if roles:
            role_label = " & ".join(roles)

    messages.success(request, f"⚡ Switched to {target_user.get_full_name() or target_user.username} ({role_label})")
    next_url = request.GET.get('next')
    if next_url and next_url != request.path and not next_url.startswith('/switch-user/') and url_has_allowed_host_and_scheme(next_url, {request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect('dashboard')




def send_verification_email(user):
    if not user.email:
        return
    token = signing.dumps({'user': user.pk, 'email': user.email}, salt='email-verification')
    url = settings.SITE_URL.rstrip('/') + reverse('verify_email', args=[token])
    send_mail('Verify your MentorPulse email',
        f'Hello {user.first_name or user.username},\n\nVerify your email within 24 hours: {url}\n',
        settings.DEFAULT_FROM_EMAIL, [user.email])


@login_required
@require_POST
def resend_verification_view(request):
    last_sent = request.session.get('verification_sent_at', 0)
    now = timezone.now().timestamp()
    if request.user.profile.email_verified:
        messages.info(request, 'Your email is already verified.')
    elif now - last_sent < 60:
        messages.info(request, 'Please wait a minute before requesting another email.')
    elif not request.user.email:
        messages.error(request, 'Add an email address to your profile first.')
    else:
        send_verification_email(request.user)
        request.session['verification_sent_at'] = now
        messages.success(request, 'Verification email sent. Check your inbox.')
    return redirect('account_settings')


def verify_email_view(request, token):
    try:
        data = signing.loads(token, salt='email-verification', max_age=86400)
        user = User.objects.get(pk=data['user'], email=data['email'], is_active=True)
    except (signing.BadSignature, User.DoesNotExist, KeyError):
        return render(request, 'accounts/verification_result.html', {'verified': False}, status=400)
    user.profile.email_verified = True
    user.profile.save(update_fields=['email_verified'])
    return render(request, 'accounts/verification_result.html', {'verified': True})


@login_required
def account_settings_view(request):
    return render(request, 'accounts/settings.html', {'profile': request.user.profile})


@login_required
def mentor_verification_request_view(request):
    profile = request.user.profile
    if not profile.is_mentor:
        return HttpResponseForbidden('Activate your mentor role first.')
    if request.method == 'POST':
        evidence = request.POST.get('evidence', '').strip()
        if len(evidence) < 20 or len(evidence) > 4000:
            return render(request, 'accounts/mentor_verification.html', {'profile': profile, 'error': 'Describe your experience and include evidence (20–4000 characters).', 'evidence': evidence})
        if not profile.mentor_verified:
            profile.verification_requested = True
            profile.verification_evidence = evidence
            profile.save(update_fields=['verification_requested', 'verification_evidence'])
        messages.success(request, 'Your verification request is available for administrator review.')
        return redirect('account_settings')
    return render(request, 'accounts/mentor_verification.html', {'profile': profile})


@login_required
def report_user_view(request, user_id):
    target = get_object_or_404(User, pk=user_id, is_active=True)
    if target == request.user:
        return HttpResponseForbidden('You cannot report yourself.')
    form = UserReportForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.reporter = request.user
        report.reported_user = target
        report.save()
        messages.success(request, 'Your report was submitted privately for administrator review.')
        return redirect('profile_user', username=target.username)
    return render(request, 'accounts/report.html', {'form': form, 'target': target})


@login_required
def availability_settings_view(request):
    if not request.user.profile.is_mentor:
        return HttpResponseForbidden('Availability slots are for active mentors.')
    form = AvailabilitySlotForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        overlaps = request.user.availability_slots.filter(weekday=form.cleaned_data['weekday'],
            start_time__lt=form.cleaned_data['end_time'], end_time__gt=form.cleaned_data['start_time']).exists()
        if overlaps:
            form.add_error(None, 'This slot overlaps an existing availability window.')
        else:
            slot = form.save(commit=False)
            slot.user = request.user
            slot.save()
            messages.success(request, 'Availability window added.')
            return redirect('availability_settings')
    return render(request, 'accounts/availability.html', {'form': form, 'slots': request.user.availability_slots.all()})


@login_required
@require_POST
def availability_delete_view(request, slot_id):
    get_object_or_404(AvailabilitySlot, pk=slot_id, user=request.user).delete()
    messages.success(request, 'Availability window removed.')
    return redirect('availability_settings')


@login_required
@require_POST
def save_mentor_view(request, mentor_id):
    mentor = get_object_or_404(User, pk=mentor_id, is_active=True)
    if mentor == request.user or not mentor.profile.is_mentor:
        return HttpResponseForbidden('Choose another active mentor.')
    if request.POST.get('action') == 'remove':
        SavedMentor.objects.filter(user=request.user, mentor=mentor).delete()
        messages.success(request, 'Mentor removed from your saved list.')
    else:
        SavedMentor.objects.get_or_create(user=request.user, mentor=mentor)
        messages.success(request, 'Mentor saved.')
    return redirect('mentor_detail', user_id=mentor.pk)
