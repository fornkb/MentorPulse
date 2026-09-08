from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from .models import Profile, Skill, RoleAssignment
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserUpdateForm,
    ProfileEditForm,
    RoleToggleForm
)


def register_view(request):
    """Handle new user registration with initial role assignment."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
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
    return render(request, 'accounts/profile_detail.html', context)


@login_required
def profile_edit_view(request):
    """Edit user details, skills, bio, availability, and active roles."""
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = ProfileEditForm(request.POST, instance=profile)
        role_form = RoleToggleForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid() and role_form.is_valid():
            user_form.save()
            profile_form.save()

            # Handle role updates
            is_mentor = role_form.cleaned_data['is_mentor']
            is_learner = role_form.cleaned_data['is_learner']

            # Mentor role
            mentor_assignment = user.role_assignments.filter(role='Mentor', end_time__isnull=True).first()
            if is_mentor and not mentor_assignment:
                RoleAssignment.objects.create(user=user, role='Mentor', context='Activated in profile settings')
            elif not is_mentor and mentor_assignment:
                mentor_assignment.end_time = timezone.now()
                mentor_assignment.save()

            # Learner role
            learner_assignment = user.role_assignments.filter(role='Learner', end_time__isnull=True).first()
            if is_learner and not learner_assignment:
                RoleAssignment.objects.create(user=user, role='Learner', context='Activated in profile settings')
            elif not is_learner and learner_assignment:
                learner_assignment.end_time = timezone.now()
                learner_assignment.save()

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

    current_skill_ids = set(profile.skills.values_list('id', flat=True))

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'role_form': role_form,
        'skills_by_category': skills_by_category,
        'current_skill_ids': current_skill_ids,
    }
    return render(request, 'accounts/profile_edit.html', context)
