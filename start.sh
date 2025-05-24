#!/bin/bash
gunicorn event_platform.wsgi:application &
celery -A event_platform worker --loglevel=info &
celery -A event_platform beat --loglevel=info &
wait