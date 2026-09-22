from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.http import HttpResponseForbidden
from mentorship.models import Mentorship
from .models import Credit, CreditTransaction, Feedback, Badge, UserBadge, LeaderboardEntry
from .forms import FeedbackForm
from .services import CreditService, FeedbackService, BadgeService, LeaderboardService


@login_required
def wallet_view(request):
    """Credit Wallet dashboard showing current balance, stats, and transaction ledger."""
    credit = CreditService.get_or_create_credit(request.user)
    transactions = request.user.credit_transactions.all().order_by('-created_at')

    # Earnings & spending statistics
    total_earned = transactions.filter(amount__gt=0).aggregate(Sum('amount'))['amount__sum'] or 0
    total_spent = abs(transactions.filter(amount__lt=0).aggregate(Sum('amount'))['amount__sum'] or 0)

    context = {
        'credit': credit,
        'transactions': transactions,
        'total_earned': total_earned,
        'total_spent': total_spent,
    }
    return render(request, 'gamification/wallet.html', context)


def leaderboard_view(request):
    """Real-time platform leaderboard with podium and ranked participants."""
    LeaderboardService.recalculate_leaderboard()

    query = request.GET.get('q', '').strip()
    entries_qs = LeaderboardEntry.objects.select_related('user__profile', 'user__credit').prefetch_related('user__user_badges').order_by('rank')

    if query:
        entries_qs = entries_qs.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    # Top 3 podium
    podium_entries = list(entries_qs[:3]) if not query else []

    # Current user position
    user_entry = None
    if request.user.is_authenticated:
        user_entry = LeaderboardEntry.objects.filter(user=request.user).first()

    context = {
        'podium_entries': podium_entries,
        'entries': entries_qs,
        'user_entry': user_entry,
        'search_query': query,
    }
    return render(request, 'gamification/leaderboard.html', context)


@login_required
def badges_view(request):
    """Achievements showcase displaying unlocked badges in color and locked ones in greyscale."""
    BadgeService.seed_core_badges()
    BadgeService.check_and_award_badges(request.user)

    all_badges = Badge.objects.all().order_by('id')
    user_badges_map = {
        ub.badge_id: ub.earned_date for ub in request.user.user_badges.all()
    }

    badges_data = []
    unlocked_count = 0

    for b in all_badges:
        is_unlocked = b.id in user_badges_map
        if is_unlocked:
            unlocked_count += 1
        badges_data.append({
            'badge': b,
            'is_unlocked': is_unlocked,
            'earned_date': user_badges_map.get(b.id),
        })

    context = {
        'badges_data': badges_data,
        'total_badges_count': all_badges.count(),
        'unlocked_count': unlocked_count,
    }
    return render(request, 'gamification/badges.html', context)


@login_required
def feedback_submit_view(request, mentorship_id):
    """Submit rating and review for collaboration."""
    mentorship = get_object_or_404(Mentorship, id=mentorship_id)
    if not mentorship.can_access(request.user):
        return HttpResponseForbidden()

    # Prevent duplicate reviews from the same participant
    if mentorship.feedbacks.filter(given_by=request.user).exists():
        messages.warning(request, "You have already submitted feedback for this mentorship.")
        return redirect('mentorship_workspace', mentorship_id=mentorship.id)

    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            rating = int(form.cleaned_data['rating'])
            comment = form.cleaned_data['comment']
            FeedbackService.submit_feedback(
                mentorship=mentorship,
                given_by=request.user,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Thank you for your rating! Your review has been published and reputation scores updated.")
        else:
            messages.error(request, "Please check the feedback form values.")

    return redirect('mentorship_workspace', mentorship_id=mentorship.id)
