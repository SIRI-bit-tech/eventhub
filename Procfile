web: gunicorn event_platform.wsgi:application
worker: celery -A event_platform worker --loglevel=info
beat: celery -A event_platform beat --loglevel=info
