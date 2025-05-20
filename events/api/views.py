from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q

from events.models import Event, RSVP, UserProfile
from .serializers import (
    EventSerializer, EventDetailSerializer, RSVPSerializer,
    UserProfileSerializer
)


class IsOrganizerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow organizers of an event to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the organizer
        return obj.organizer == request.user


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOrganizerOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'location', 'category']
    ordering_fields = ['start_time', 'created_at', 'title']
    ordering = ['start_time']

    def get_queryset(self):
        queryset = Event.objects.all()

        # Filter by public events for non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)

        # Filter by category if provided
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by upcoming events
        upcoming = self.request.query_params.get('upcoming', None)
        if upcoming:
            queryset = queryset.filter(end_time__gte=timezone.now())

        # Filter by user's events
        user_events = self.request.query_params.get('user', None)
        if user_events and self.request.user.is_authenticated:
            if user_events == 'organized':
                queryset = queryset.filter(organizer=self.request.user)
            elif user_events == 'attending':
                queryset = queryset.filter(
                    rsvps__user=self.request.user,
                    rsvps__status='attending'
                )

        # Annotate with attendee count
        queryset = queryset.annotate(
            attendee_count=Count('rsvps', filter=Q(rsvps__status='attending'))
        )

        return queryset

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return EventDetailSerializer
        return EventSerializer

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rsvp(self, request, pk=None):
        event = self.get_object()
        user = request.user
        status_value = request.data.get('status', 'attending')

        # Check if event is full
        if status_value == 'attending' and event.is_full:
            return Response(
                {'detail': 'This event is already full.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get or create RSVP
        try:
            rsvp = RSVP.objects.get(user=user, event=event)
            rsvp.status = status_value
            rsvp.save()
        except RSVP.DoesNotExist:
            rsvp = RSVP.objects.create(
                user=user,
                event=event,
                status=status_value
            )

        serializer = RSVPSerializer(rsvp)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def user_rsvp(self, request, pk=None):
        event = self.get_object()
        user = request.user

        try:
            rsvp = RSVP.objects.get(user=user, event=event)
            serializer = RSVPSerializer(rsvp)
            return Response(serializer.data)
        except RSVP.DoesNotExist:
            return Response(
                {'detail': 'You have not RSVP\'d to this event.'},
                status=status.HTTP_404_NOT_FOUND
            )


class UserProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user profiles to be viewed or edited.
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def me(self, request):
        profile = get_object_or_404(UserProfile, user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)