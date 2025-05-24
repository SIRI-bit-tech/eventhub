from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Event


@login_required
def calendar_view(request):
    """View for displaying user's events in a calendar format"""
    return render(request, 'events/calendar.html')


@login_required
def get_user_events(request):
    """API endpoint to get user's events for calendar"""
    # Get events organized by the user
    organized_events = Event.objects.filter(organizer=request.user)

    # Get events the user is attending
    attending_events = Event.objects.filter(
        rsvps__user=request.user,
        rsvps__status='attending'
    ).exclude(organizer=request.user)

    # Combine and format events for calendar
    events = []

    for event in organized_events:
        events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'url': f'/events/{event.id}/',
            'backgroundColor': '#6d28d9',  # Primary color for organized events
            'borderColor': '#5b21b6',
        })

    for event in attending_events:
        events.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'url': f'/events/{event.id}/',
            'backgroundColor': '#10b981',  # Secondary color for attending events
            'borderColor': '#059669',
        })

    return JsonResponse(events, safe=False)


@csrf_exempt
def google_calendar_sync(request):
    """Endpoint for Google Calendar sync"""
    if request.method == 'POST':
        # This would handle Google Calendar sync
        # Implementation would depend on your Google Calendar integration
        return JsonResponse({'status': 'success'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)