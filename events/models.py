from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from pyuploadcare.dj.models import ImageField


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('meetup', 'Meetup'),
        ('social', 'Social'),
        ('sports', 'Sports'),
        ('arts', 'Arts & Culture'),
        ('business', 'Business'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('health', 'Health & Wellness'),
        ('other', 'Other'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events')
    location = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    image = ImageField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('event_detail', kwargs={'pk': self.pk})

    @property
    def is_past(self):
        return self.end_time < timezone.now()

    @property
    def attendee_count(self):
        return self.rsvps.filter(status='attending').count()

    @property
    def is_full(self):
        if self.max_attendees:
            return self.attendee_count >= self.max_attendees
        return False


class RSVP(models.Model):
    STATUS_CHOICES = (
        ('attending', 'Attending'),
        ('maybe', 'Maybe'),
        ('declined', 'Declined'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rsvps')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='rsvps')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='attending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.username} - {self.event.title} - {self.status}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True)
    profile_picture = ImageField(null=True, blank=True, manual_crop="1:1")
    interests = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    receive_event_notifications = models.BooleanField(default=True)
    receive_reminders = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s profile"
