from django.urls import path
from . import views, views_calendar

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('event/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('event/new/', views.EventCreateView.as_view(), name='event_create'),
    path('event/<int:pk>/update/', views.EventUpdateView.as_view(), name='event_update'),
    path('event/<int:pk>/delete/', views.EventDeleteView.as_view(), name='event_delete'),
    path('event/<int:pk>/rsvp/', views.rsvp_event, name='rsvp_event'),
    path('profile/', views.profile_view, name='profile'),
    path('register/', views.register, name='register'),

    # HTMX endpoints
    path('events/category/', views.load_events_by_category, name='load_events_by_category'),
    path('event/<int:pk>/toggle-attendance/', views.toggle_attendance, name='toggle_attendance'),

    # Google Calendar integration
    path('calendar/init/', views_calendar.google_calendar_init, name='google_calendar_init'),
    path('calendar/callback/', views_calendar.google_calendar_callback, name='google_calendar_callback'),
    path('calendar/events/', views_calendar.google_calendar_events, name='google_calendar_events'),
    path('event/<int:pk>/add-to-calendar/', views_calendar.add_event_to_google_calendar, name='add_event_to_calendar'),
]