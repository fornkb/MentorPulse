"""
Matching Engine Service for MentorPulse.
Implements deterministic, rule-based matching between learners and mentors.
"""
from accounts.models import Profile, Skill

EXP_LEVELS = {
    'Beginner': 1,
    'Intermediate': 2,
    'Advanced': 3,
    'Expert': 4,
}


def calculate_match_score(learner_profile: Profile, mentor_profile: Profile) -> dict:
    """
    Calculate compatibility score (0 - 100%) between a learner and a mentor.
    
    Weights:
    - Skill Overlap: 50%
    - Availability Compatibility: 30%
    - Experience Affinity: 20%
    """
    if not learner_profile or not mentor_profile:
        return {
            'total_score': 50,
            'skill_percentage': 50,
            'availability_percentage': 50,
            'experience_percentage': 50,
            'shared_skills': [],
            'shared_skill_count': 0,
        }

    # 1. Skill Overlap (50%)
    learner_skills = set(learner_profile.skills.all())
    mentor_skills = set(mentor_profile.skills.all())
    shared_skills = list(learner_skills & mentor_skills)

    if learner_skills:
        skill_ratio = len(shared_skills) / len(learner_skills)
    else:
        # Default baseline if learner hasn't selected skills yet
        skill_ratio = 0.5

    # 2. Availability Compatibility (30%)
    l_avail = (learner_profile.availability or '').strip().lower()
    m_avail = (mentor_profile.availability or '').strip().lower()

    if l_avail and m_avail and l_avail == m_avail:
        avail_ratio = 1.0
    elif 'flexible' in l_avail or 'flexible' in m_avail:
        avail_ratio = 0.9
    elif not l_avail or not m_avail:
        avail_ratio = 0.6
    else:
        avail_ratio = 0.2

    # 3. Experience Affinity (20%)
    l_lvl = EXP_LEVELS.get(learner_profile.experience_level, 1)
    m_lvl = EXP_LEVELS.get(mentor_profile.experience_level, 3)
    diff = m_lvl - l_lvl

    if diff in (1, 2):
        # Ideal mentor growth margin (1-2 tiers higher)
        exp_ratio = 1.0
    elif diff == 3:
        # Expert mentor with Beginner learner
        exp_ratio = 0.9
    elif diff == 0:
        # Peer mentorship
        exp_ratio = 0.65
    else:
        # Mentor has lower experience than learner
        exp_ratio = 0.25

    # Calculate total composite score
    total_score = round(
        (skill_ratio * 50.0) +
        (avail_ratio * 30.0) +
        (exp_ratio * 20.0)
    )
    total_score = max(0, min(100, total_score))

    return {
        'total_score': total_score,
        'skill_percentage': round(skill_ratio * 100),
        'availability_percentage': round(avail_ratio * 100),
        'experience_percentage': round(exp_ratio * 100),
        'shared_skills': shared_skills,
        'shared_skill_count': len(shared_skills),
    }


def rank_mentors_for_learner(learner_user, mentors_queryset) -> list:
    """
    Ranks a queryset of mentor users according to their match score for a given learner.
    If learner_user is None, anonymous, or lacks a profile, scores default to skill_score or baseline.
    Returns a list of dicts: [{'mentor': user, 'profile': profile, 'match': score_data, 'score': total_score}, ...]
    """
    results = []
    learner_profile = getattr(learner_user, 'profile', None) if (learner_user and learner_user.is_authenticated) else None

    for mentor in mentors_queryset:
        mentor_profile = getattr(mentor, 'profile', None)
        if not mentor_profile:
            continue

        if learner_profile:
            score_data = calculate_match_score(learner_profile, mentor_profile)
        else:
            # Baseline for anonymous or unauthenticated visitors
            baseline = min(100, int(50 + (mentor_profile.skill_score * 5)))
            score_data = {
                'total_score': baseline,
                'skill_percentage': baseline,
                'availability_percentage': 70,
                'experience_percentage': 70,
                'shared_skills': [],
                'shared_skill_count': 0,
            }

        results.append({
            'mentor': mentor,
            'profile': mentor_profile,
            'match': score_data,
            'score': score_data['total_score'],
        })

    # Sort primarily by match score descending, then by mentor skill score descending
    results.sort(key=lambda item: (item['score'], item['profile'].skill_score), reverse=True)
    return results
