from django.urls import path, include
from . import views, views_calendar
from rest_framework.routers import DefaultRouter

# Create a router for REST API
router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'rsvps', views.RSVPViewSet, basename='rsvp')

urlpatterns = [
    # Main views
    path('', views.home, name='home'),  # Changed from HomeView.as_view() to home
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<int:pk>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:pk>/rsvp/', views.rsvp_event, name='rsvp_event'),
    path('events/<int:pk>/add-to-calendar/', views.add_event_to_calendar, name='add_event_to_calendar'),
    path('events/<int:pk>/download-ics/', views.download_ics, name='download_ics'),

    # HTMX partials
    path('events/list/', views.event_list_partial, name='event_list_partial'),
    path('events/by-category/', views.load_events_by_category, name='load_events_by_category'),



    # User account views
    path('register/', views.register, name='register'),
    path('profile/', views.profile_view, name='profile'),

    # Calendar views
    path('calendar/', views_calendar.calendar_view, name='calendar'),
    path('calendar/events/', views_calendar.get_user_events, name='calendar_events'),
    path('calendar/sync/', views_calendar.google_calendar_sync, name='calendar_sync'),

    # Google Calendar webhook
    path('webhooks/google-calendar/', views.google_calendar_webhook, name='google_calendar_webhook'),

    # REST API
    path('api/', include(router.urls)),
]