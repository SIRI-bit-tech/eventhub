from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from events.models import Event, RSVP


def send_html_email(subject, template_name, context, recipient_list):
    """
    Send an HTML email using a template
    """
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list
    )
    email.attach_alternative(html_content, "text/html")
    return email.send()


def send_event_created_notification(event):
    """
    Send notification when a new event is created
    """
    subject = f"New Event: {event.title}"
    template_name = 'emails/event_created.html'
    context = {
        'event': event,
    }

    # Get all users except the organizer
    recipients = User.objects.exclude(id=event.organizer.id).values_list('email', flat=True)

    if recipients:
        send_html_email(subject, template_name, context, recipients)


def send_event_updated_notification(event):
    """
    Send notification when an event is updated
    """
    subject = f"Event Updated: {event.title}"
    template_name = 'emails/event_updated.html'
    context = {
        'event': event,
    }

    # Get all users who have RSVP'd to this event
    recipients = RSVP.objects.filter(event=event).values_list('user__email', flat=True)

    if recipients:
        send_html_email(subject, template_name, context, recipients)


def send_event_reminder(event):
    """
    Send a reminder 24 hours before an event
    """
    subject = f"Reminder: {event.title} is tomorrow!"
    template_name = 'emails/event_reminder.html'
    context = {
        'event': event,
    }

    # Get all users who are attending this event
    recipients = RSVP.objects.filter(event=event, status='attending').values_list('user__email', flat=True)

    if recipients:
        send_html_email(subject, template_name, context, recipients)


def send_rsvp_confirmation(rsvp):
    """
    Send confirmation when a user RSVPs to an event
    """
    subject = f"RSVP Confirmation: {rsvp.event.title}"
    template_name = 'emails/rsvp_confirmation.html'
    context = {
        'rsvp': rsvp,
        'event': rsvp.event,
    }

    send_html_email(subject, template_name, context, [rsvp.user.email])


def send_event_canceled_notification(event, recipients):
    """
    Send notification when an event is canceled
    """
    subject = f"Event Canceled: {event.title}"
    template_name = 'emails/event_canceled.html'
    context = {
        'event': event,
    }

    if recipients:
        send_html_email(subject, template_name, context, recipients)