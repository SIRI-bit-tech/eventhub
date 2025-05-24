# import eventlet
# eventlet.monkey_patch()

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'event_platform.settings')

app = Celery('event_platform')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'send-event-reminders-daily': {
        'task': 'events.tasks.send_event_reminders',
        'schedule': 86400.0,  # 24 hours
    },
    'clean-old-events-weekly': {
        'task': 'events.tasks.clean_old_events',
        'schedule': 604800.0,  # 7 days
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')