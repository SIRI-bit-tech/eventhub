from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth.models import User
from .models import Event, RSVP
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_event_notification(event_id, message):
    """
    Send notification email about an event
    """
    try:
        event = Event.objects.get(id=event_id)

        # Send to event organizer
        subject = f'EventHub: Notification for {event.title}'

        html_message = render_to_string('emails/event_notification.html', {
            'event': event,
            'message': message,
            'site_url': settings.SITE_URL,
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[event.organizer.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f'Event notification sent for event {event_id}')
        return f'Notification sent for event: {event.title}'

    except Event.DoesNotExist:
        logger.error(f'Event with id {event_id} does not exist')
        return f'Event with id {event_id} not found'
    except Exception as e:
        logger.error(f'Error sending event notification: {str(e)}')
        return f'Error sending notification: {str(e)}'


@shared_task
def send_event_reminder(event_id):
    """
    Send reminder email to all attendees of an event
    """
    try:
        event = Event.objects.get(id=event_id)

        # Get all attendees
        attendees = User.objects.filter(
            rsvp__event=event,
            rsvp__status='attending'
        ).distinct()

        if not attendees.exists():
            return f'No attendees found for event: {event.title}'

        subject = f'Reminder: {event.title} is coming up!'

        for attendee in attendees:
            # Check if user wants to receive reminders
            if hasattr(attendee, 'profile') and not attendee.profile.receive_reminders:
                continue

            html_message = render_to_string('emails/event_reminder.html', {
                'event': event,
                'user': attendee,
                'site_url': settings.SITE_URL,
            })
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[attendee.email],
                html_message=html_message,
                fail_silently=False,
            )

        logger.info(f'Event reminders sent for event {event_id} to {attendees.count()} attendees')
        return f'Reminders sent for event: {event.title} to {attendees.count()} attendees'

    except Event.DoesNotExist:
        logger.error(f'Event with id {event_id} does not exist')
        return f'Event with id {event_id} not found'
    except Exception as e:
        logger.error(f'Error sending event reminders: {str(e)}')
        return f'Error sending reminders: {str(e)}'


@shared_task
def send_event_update_notification(event_id, update_message):
    """
    Send notification to all attendees when an event is updated
    """
    try:
        event = Event.objects.get(id=event_id)

        # Get all attendees
        attendees = User.objects.filter(
            rsvp__event=event,
            rsvp__status='attending'
        ).distinct()

        if not attendees.exists():
            return f'No attendees found for event: {event.title}'

        subject = f'Update: {event.title} has been modified'

        for attendee in attendees:
            # Check if user wants to receive event notifications
            if hasattr(attendee, 'profile') and not attendee.profile.receive_event_notifications:
                continue

            html_message = render_to_string('emails/event_update.html', {
                'event': event,
                'user': attendee,
                'update_message': update_message,
                'site_url': settings.SITE_URL,
            })
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[attendee.email],
                html_message=html_message,
                fail_silently=False,
            )

        logger.info(f'Event update notifications sent for event {event_id} to {attendees.count()} attendees')
        return f'Update notifications sent for event: {event.title} to {attendees.count()} attendees'

    except Event.DoesNotExist:
        logger.error(f'Event with id {event_id} does not exist')
        return f'Event with id {event_id} not found'
    except Exception as e:
        logger.error(f'Error sending event update notifications: {str(e)}')
        return f'Error sending update notifications: {str(e)}'


@shared_task
def send_welcome_email(user_id):
    """
    Send welcome email to new users
    """
    try:
        user = User.objects.get(id=user_id)

        subject = 'Welcome to EventHub!'

        html_message = render_to_string('emails/welcome.html', {
            'user': user,
            'site_url': settings.SITE_URL,
        })
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f'Welcome email sent to user {user_id}')
        return f'Welcome email sent to: {user.email}'

    except User.DoesNotExist:
        logger.error(f'User with id {user_id} does not exist')
        return f'User with id {user_id} not found'
    except Exception as e:
        logger.error(f'Error sending welcome email: {str(e)}')
        return f'Error sending welcome email: {str(e)}'


@shared_task
def cleanup_expired_events():
    """
    Cleanup task to handle expired events
    """
    from django.utils import timezone
    from datetime import timedelta

    try:
        # Find events that ended more than 30 days ago
        cutoff_date = timezone.now() - timedelta(days=30)
        expired_events = Event.objects.filter(end_time__lt=cutoff_date)

        count = expired_events.count()

        # You can add cleanup logic here, such as:
        # - Archiving old events
        # - Sending summary emails
        # - Cleaning up associated data

        logger.info(f'Found {count} expired events for cleanup')
        return f'Processed {count} expired events'

    except Exception as e:
        logger.error(f'Error in cleanup task: {str(e)}')
        return f'Error in cleanup: {str(e)}'


@shared_task
def send_daily_digest():
    """
    Send daily digest of upcoming events to users
    """
    from django.utils import timezone
    from datetime import timedelta

    try:
        # Get events happening in the next 7 days
        start_date = timezone.now()
        end_date = start_date + timedelta(days=7)

        upcoming_events = Event.objects.filter(
            start_time__gte=start_date,
            start_time__lte=end_date,
            is_public=True
        ).order_by('start_time')

        if not upcoming_events.exists():
            return 'No upcoming events for digest'

        # Get users who want to receive notifications
        users = User.objects.filter(
            profile__receive_event_notifications=True
        ).distinct()

        subject = 'EventHub: Your Weekly Event Digest'

        for user in users:
            html_message = render_to_string('emails/weekly_digest.html', {
                'user': user,
                'events': upcoming_events,
                'site_url': settings.SITE_URL,
            })
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

        logger.info(f'Weekly digest sent to {users.count()} users')
        return f'Weekly digest sent to {users.count()} users'

    except Exception as e:
        logger.error(f'Error sending daily digest: {str(e)}')
        return f'Error sending digest: {str(e)}'