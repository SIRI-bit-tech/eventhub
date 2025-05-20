import os
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseRedirect
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.errors import HttpError

from .utils.google_calendar import get_oauth_flow, get_upcoming_events, create_event_in_google_calendar
from .models import Event


@login_required
def google_calendar_init(request):
    """
    Initiates the OAuth flow for Google Calendar
    """
    # Build the redirect URI
    redirect_uri = request.build_absolute_uri(reverse('google_calendar_callback'))

    # Create the flow
    flow = get_oauth_flow(redirect_uri)

    # Generate the authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    # Store the state in the session
    request.session['google_auth_state'] = state

    # Redirect to the authorization URL
    return redirect(authorization_url)


@login_required
def google_calendar_callback(request):
    """
    Handles the callback from Google OAuth
    """
    # Get the state from the session
    state = request.session.get('google_auth_state')

    # Build the redirect URI
    redirect_uri = request.build_absolute_uri(reverse('google_calendar_callback'))

    # Create the flow
    flow = get_oauth_flow(redirect_uri)

    # Use the authorization code to get credentials
    flow.fetch_token(
        authorization_response=request.build_absolute_uri(),
        state=state
    )

    # Get the credentials
    credentials = flow.credentials

    # Store the credentials in the session
    request.session['google_credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    # Redirect to the calendar events page
    return redirect('google_calendar_events')


@login_required
def google_calendar_events(request):
    """
    Displays upcoming events from the user's Google Calendar
    """
    # Get the credentials from the session
    credentials_dict = request.session.get('google_credentials')

    if not credentials_dict:
        # If no credentials, redirect to the init view
        return redirect('google_calendar_init')

    # Create credentials object
    credentials = Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict['refresh_token'],
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )

    try:
        # Get upcoming events
        events = get_upcoming_events(credentials)

        # Render the events
        return render(request, 'events/google_calendar_events.html', {
            'events': events
        })
    except HttpError as error:
        # If the credentials are invalid, redirect to the init view
        if error.resp.status in [401, 403]:
            return redirect('google_calendar_init')

        # Otherwise, render an error page
        return render(request, 'events/google_calendar_error.html', {
            'error': error
        })


@login_required
def add_event_to_google_calendar(request, pk):
    """
    Adds an event to the user's Google Calendar
    """
    # Get the event
    event = Event.objects.get(pk=pk)

    # Get the credentials from the session
    credentials_dict = request.session.get('google_credentials')

    if not credentials_dict:
        # If no credentials, redirect to the init view
        return redirect('google_calendar_init')

    # Create credentials object
    credentials = Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict['refresh_token'],
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )

    try:
        # Create the event in Google Calendar
        created_event = create_event_in_google_calendar(credentials, event)

        # Redirect to the event detail page with a success message
        return redirect('event_detail', pk=pk)
    except HttpError as error:
        # If the credentials are invalid, redirect to the init view
        if error.resp.status in [401, 403]:
            return redirect('google_calendar_init')

        # Otherwise, render an error page
        return render(request, 'events/google_calendar_error.html', {
            'error': error
        })