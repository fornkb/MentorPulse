import os
from django import forms
from django.core.exceptions import ValidationError
from .models import Mentorship, Session, Milestone, Resource, DiscussionPost

ALLOWED_EXTENSIONS = ['.pdf', '.png', '.jpg', '.jpeg', '.txt', '.docx', '.doc']
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class MentorshipRequestForm(forms.ModelForm):
    goals = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Share your background, current challenges, and specific skills you want to develop during this mentorship...'
        }),
        help_text="Clear goals help mentors review and tailor your collaborative milestones."
    )
    is_priority = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        help_text="Flag this request with priority status to highlight it in the mentor's inbox."
    )

    class Meta:
        model = Mentorship
        fields = ['goals', 'is_priority']


class SessionForm(forms.ModelForm):
    date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        }),
        help_text="Select proposed meeting date and time."
    )
    meeting_link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={
            'class': 'form-control',
            'placeholder': 'https://meet.google.com/abc-defg-hij or Zoom link'
        }),
        help_text="Video meeting link (Google Meet, Zoom, MS Teams, etc.)"
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Meeting agenda, preparation checklist, or discussion topics...'
        })
    )

    class Meta:
        model = Session
        fields = ['date', 'meeting_link', 'notes']


class MilestoneForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Build prototype and write unit tests'
        })
    )

    class Meta:
        model = Milestone
        fields = ['title']


class ResourceForm(forms.ModelForm):
    title = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Resource Title'
        })
    )
    type = forms.ChoiceField(
        choices=Resource.TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    content = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Paste URL for web links, or write quick notes/markdown instructions'
        })
    )
    file = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Resource
        fields = ['title', 'type', 'content', 'file']

    def clean_file(self):
        uploaded_file = self.cleaned_data.get('file')
        if uploaded_file:
            # 1. Validate file size (<= 10MB)
            if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                raise ValidationError("File size exceeds 10MB limit. Please upload a smaller file.")

            # 2. Validate file extension
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f"Unsupported file format '{ext}'. Allowed formats: {', '.join(ALLOWED_EXTENSIONS)}"
                )
        return uploaded_file

    def clean(self):
        cleaned_data = super().clean()
        rtype = cleaned_data.get('type')
        content = cleaned_data.get('content')
        uploaded_file = cleaned_data.get('file')

        if rtype == 'LINK' and not content:
            self.add_error('content', "Please provide a valid URL for Web Link resources.")
        elif rtype == 'FILE' and not uploaded_file:
            self.add_error('file', "Please attach a file for File Upload resources.")
        elif rtype == 'NOTE' and not content:
            self.add_error('content', "Please enter the note or instructions text.")

        return cleaned_data


class DiscussionPostForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Write a message or update for your mentorship pair...'
        })
    )

    class Meta:
        model = DiscussionPost
        fields = ['text']
