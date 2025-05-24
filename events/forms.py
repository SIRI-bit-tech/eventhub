from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from pyuploadcare.dj.forms import FileWidget, ImageField
from .models import Event, RSVP, UserProfile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']

        if commit:
            user.save()
            # The signal will handle profile creation

        return user


class EventForm(forms.ModelForm):
    # Use Uploadcare ImageField with explicit widget
    image = ImageField(label='Event Image', required=False, widget=FileWidget(attrs={
        'data-images-only': 'true',
        'data-preview-step': 'true',
        'data-crop': 'free',
    }))

    class Meta:
        model = Event
        fields = ['title', 'description', 'location', 'start_time', 'end_time',
                  'max_attendees', 'image', 'is_public', 'category']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class RSVPForm(forms.ModelForm):
    class Meta:
        model = RSVP
        fields = ['status']


class UserProfileForm(forms.ModelForm):
    # Use Uploadcare ImageField with explicit widget
    profile_picture = ImageField(label='Profile Picture', required=False, widget=FileWidget(attrs={
        'data-images-only': 'true',
        'data-preview-step': 'true',
        'data-crop': '1:1',
        'data-validators': 'filled, imgType, maxFileSize',
        'data-max-file-size': '5242880',  # 5MB
    }))

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture', 'interests', 'location', 'receive_event_notifications', 'receive_reminders']


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']