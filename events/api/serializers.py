from rest_framework import serializers
from django.contrib.auth.models import User
from events.models import Event, RSVP, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'profile_picture', 'interests', 'location']


class RSVPSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = RSVP
        fields = ['id', 'user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class EventSerializer(serializers.ModelSerializer):
    organizer = UserSerializer(read_only=True)
    attendee_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'location', 'start_time', 'end_time',
            'created_at', 'updated_at', 'organizer', 'max_attendees', 'image',
            'is_public', 'category', 'attendee_count', 'is_full'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EventDetailSerializer(EventSerializer):
    rsvps = RSVPSerializer(many=True, read_only=True)

    class Meta(EventSerializer.Meta):
        fields = EventSerializer.Meta.fields + ['rsvps']