from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from accounts.models import Profile, Skill, RoleAssignment
from .services import calculate_match_score, rank_mentors_for_learner


def mentor_directory_view(request):
    """
    Searchable, filterable directory of active mentors.
    When a learner is authenticated, results are ranked according to the
    deterministic rule-based match scoring algorithm.
    """
    # 1. Fetch only users who hold an active Mentor role assignment
    active_mentor_ids = RoleAssignment.objects.filter(
        role='Mentor',
        end_time__isnull=True
    ).values_list('user_id', flat=True).distinct()

    mentors_qs = User.objects.filter(id__in=active_mentor_ids).select_related('profile').prefetch_related('profile__skills')

    # 2. Extract filter parameters
    query = request.GET.get('q', '').strip()
    skill_filter = request.GET.get('skill', '').strip()
    exp_filter = request.GET.get('experience', '').strip()
    avail_filter = request.GET.get('availability', '').strip()

    active_filter_count = 0

    # 3. Apply search query
    if query:
        active_filter_count += 1
        mentors_qs = mentors_qs.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query) |
            Q(profile__bio__icontains=query) |
            Q(profile__skills__name__icontains=query)
        ).distinct()

    # 4. Apply skill filter
    if skill_filter:
        active_filter_count += 1
        if skill_filter.isdigit():
            mentors_qs = mentors_qs.filter(profile__skills__id=int(skill_filter)).distinct()
        else:
            mentors_qs = mentors_qs.filter(profile__skills__name__iexact=skill_filter).distinct()

    # 5. Apply experience filter
    if exp_filter:
        active_filter_count += 1
        mentors_qs = mentors_qs.filter(profile__experience_level=exp_filter)

    # 6. Apply availability filter
    if avail_filter:
        active_filter_count += 1
        mentors_qs = mentors_qs.filter(profile__availability=avail_filter)

    # 7. Rank candidate mentors
    ranked_mentors = rank_mentors_for_learner(request.user, mentors_qs)

    # 8. Prepare filter options for UI
    all_skills = Skill.objects.all().order_by('category', 'name')
    experience_choices = Profile.EXPERIENCE_CHOICES
    availability_choices = Profile.AVAILABILITY_CHOICES

    # Popular skills for quick filter tags
    popular_skills = Skill.objects.filter(profiles__user__id__in=active_mentor_ids).distinct()[:10]

    context = {
        'ranked_mentors': ranked_mentors,
        'total_mentors_count': len(ranked_mentors),
        'all_skills': all_skills,
        'popular_skills': popular_skills,
        'experience_choices': experience_choices,
        'availability_choices': availability_choices,
        'selected_q': query,
        'selected_skill': skill_filter,
        'selected_experience': exp_filter,
        'selected_availability': avail_filter,
        'active_filter_count': active_filter_count,
        'is_learner': request.user.is_authenticated and hasattr(request.user, 'profile') and request.user.profile.is_learner,
    }
    return render(request, 'matching/mentor_list.html', context)


def mentor_detail_view(request, user_id):
    """
    Detailed public profile for a mentor.
    Displays credentials, skills portfolio, availability schedule, and match score
    breakdown if the viewing user is an authenticated learner.
    """
    mentor_user = get_object_or_404(User.objects.select_related('profile').prefetch_related('profile__skills'), id=user_id)
    profile = mentor_user.profile

    # Check if mentor is actively assigned
    is_active_mentor = mentor_user.role_assignments.filter(role='Mentor', end_time__isnull=True).exists()

    # Calculate match compatibility if viewer is authenticated learner and not the mentor themselves
    match_data = None
    is_own_profile = (request.user == mentor_user)

    if request.user.is_authenticated and not is_own_profile and hasattr(request.user, 'profile'):
        match_data = calculate_match_score(request.user.profile, profile)

    # Categorize skills for structured display
    skills_by_category = {}
    for skill in profile.skills.all():
        skills_by_category.setdefault(skill.category, []).append(skill)

    context = {
        'mentor': mentor_user,
        'profile': profile,
        'skills': profile.skills.all(),
        'skills_by_category': skills_by_category,
        'is_active_mentor': is_active_mentor,
        'match_data': match_data,
        'is_own_profile': is_own_profile,
        'shared_skills': match_data.get('shared_skills', []) if match_data else [],
    }
    return render(request, 'matching/mentor_detail.html', context)
