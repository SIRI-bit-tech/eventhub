from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Event, RSVP, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'profile_picture', 'interests', 'location']


class RSVPSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RSVP
        fields = ['id', 'user', 'event', 'status', 'created_at']
        read_only_fields = ['user', 'created_at']


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    attendee_count = serializers.SerializerMethodField()
    is_full = serializers.SerializerMethodField()

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'organizer', 'location',
            'start_time', 'end_time', 'max_attendees', 'image',
            'is_public', 'category', 'created_at', 'updated_at',
            'attendee_count', 'is_full'
        ]
        read_only_fields = ['organizer', 'created_at', 'updated_at']

    def get_attendee_count(self, obj):
        return obj.attendee_count()

    def get_is_full(self, obj):
        return obj.is_full()