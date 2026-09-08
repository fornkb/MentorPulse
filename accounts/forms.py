from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import Profile, Skill, RoleAssignment


class UserRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a strong password'}),
        validators=[validate_password]
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    # Initial Role selection
    register_as_learner = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    register_as_mentor = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. alex_dev'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password') or self.data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")


        as_learner = cleaned_data.get('register_as_learner')
        as_mentor = cleaned_data.get('register_as_mentor')
        if not as_learner and not as_mentor:
            raise ValidationError("Please select at least one role: Learner or Mentor.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            # Handle roles
            as_learner = self.cleaned_data.get('register_as_learner')
            as_mentor = self.cleaned_data.get('register_as_mentor')

            # Ensure Learner assignment matches checkbox
            if as_learner and not user.role_assignments.filter(role='Learner', end_time__isnull=True).exists():
                RoleAssignment.objects.create(user=user, role='Learner', context='Selected at registration')
            elif not as_learner:
                user.role_assignments.filter(role='Learner', end_time__isnull=True).delete()

            # Ensure Mentor assignment matches checkbox
            if as_mentor and not user.role_assignments.filter(role='Mentor', end_time__isnull=True).exists():
                RoleAssignment.objects.create(user=user, role='Mentor', context='Selected at registration')

        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'})
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class ProfileEditForm(forms.ModelForm):
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Profile
        fields = ['bio', 'experience_level', 'availability', 'goals', 'skills']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Introduce yourself, your background, and your aspirations...'}),
            'experience_level': forms.Select(attrs={'class': 'form-select'}),
            'availability': forms.Select(attrs={'class': 'form-select'}),
            'goals': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'What are you hoping to achieve on MentorPulse?'}),
        }


class RoleToggleForm(forms.Form):
    is_mentor = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    is_learner = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        cleaned_data = super().clean()
        is_mentor = cleaned_data.get('is_mentor')
        is_learner = cleaned_data.get('is_learner')
        if not is_mentor and not is_learner:
            raise ValidationError("You must keep at least one active role (Mentor or Learner).")
        return cleaned_data
