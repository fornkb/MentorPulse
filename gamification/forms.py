from django import forms
from .models import Feedback


class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(
        choices=Feedback.RATING_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text="Rate your collaboration experience from 1 to 5 stars."
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Share what went well, key learnings, or words of appreciation for your mentorship partner...'
        }),
        help_text="Detailed feedback supports badge unlocking and platform reputation."
    )

    class Meta:
        model = Feedback
        fields = ['rating', 'comment']
