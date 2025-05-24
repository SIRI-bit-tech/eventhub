#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Apply database migrations
python manage.py migrate

# Create default superuser if needed (optional)
# python manage.py createsuperuser --noinput --username admin --email admin@example.com
