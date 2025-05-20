import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from django.conf import settings
from django.urls import reverse


def get_google_calendar_service(credentials):
    """
    Build and return a Google Calendar service object
    """
    service = build('calendar', 'v3', credentials=credentials)
    return service


def get_oauth_flow(redirect_uri):
    """
    Create and return an OAuth 2.0 flow object
    """
    # This would typically be loaded from a JSON file downloaded from Google Cloud Console
    client_config = {
        "web": {
            "client_id": os.environ.get("GOOGLE_CLIENT_ID", "your-client-id"),
            "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", "your-client-secret"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=['https://www.googleapis.com/auth/calendar.readonly'],
        redirect_uri=redirect_uri
    )

    return flow


def get_upcoming_events(credentials, max_results=10):
    """
    Get a list of upcoming events from the user's Google Calendar
    """
    service = get_google_calendar_service(credentials)

    # Get the current time in RFC3339 format
    now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time

    # Call the Calendar API
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    return events


def create_event_in_google_calendar(credentials, event):
    """
    Create an event in the user's Google Calendar
    """
    service = get_google_calendar_service(credentials)

    # Format the event for Google Calendar
    google_event = {
        'summary': event.title,
        'location': event.location,
        'description': event.description,
        'start': {
            'dateTime': event.start_time.isoformat(),
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': event.end_time.isoformat(),
            'timeZone': 'UTC',
        },
    }

    # Create the event
    created_event = service.events().insert(calendarId='primary', body=google_event).execute()

    return created_event