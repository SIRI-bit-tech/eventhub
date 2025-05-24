# CEMP - Comprehensive Event Management Platform

A robust Django-based event management platform designed to streamline the process of creating, managing, and attending events.

## Features

- **Event Management**: Create, update, and manage events with detailed information
- **User Authentication**: Secure user accounts with Django's authentication system
- **Task Scheduling**: Background task processing with Celery
- **Modern UI**: Responsive and clean interface using Tailwind CSS
- **Real-time Updates**: Stay informed with timely notifications

## Technology Stack

- **Backend**: Django
- **Frontend**: 
  - Tailwind CSS (v3.2.7)
  - Tailwind plugins:
    - @tailwindcss/forms (v0.5.3)
    - @tailwindcss/typography (v0.5.2)
    - @tailwindcss/line-clamp (v0.4.2)
    - @tailwindcss/aspect-ratio (v0.4.2)
  - PostCSS (v8.4.14)
- **Task Queue**: Celery (v5.3.4)
- **CSS Processing**:
  - postcss-import (v15.1.0)
  - postcss-nested (v6.0.0)
  - postcss-simple-vars (v7.0.1)

## Prerequisites

- Python 3.x
- Node.js and npm
- Redis (for Celery task broker)
- PostgreSQL (recommended for production)

## Installation

1. **Clone the repository**:
   ```bash
   git clone <https://github.com/SIRI-bit-tech/eventhub>
   cd CEMP
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

5. **Configure environment variables**:
   Create a `.env` file in the root directory with the following variables:
   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_URL=sqlite:///db.sqlite3  # Use PostgreSQL for production
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   ```

6. **Apply database migrations**:
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser** (for admin access):
   ```bash
   python manage.py createsuperuser
   ```

8. **Compile static files**:
   ```bash
   python manage.py collectstatic
   ```

## Running the Development Server

1. **Start the Django development server**:
   ```bash
   python manage.py runserver
   ```

2. **Start Celery worker**:
   ```bash
   celery -A event_platform worker -l info
   ```

3. **Start Celery beat** (for scheduled tasks):
   ```bash
   celery -A event_platform beat -l info
   ```

## Project Structure

- `event_platform/` - Main Django project configuration
- `events/` - Event management application
- `templates/` - HTML templates
- `static/` - Static files (CSS, JavaScript, images)
- `theme/` - Tailwind CSS configuration and styles
- `manage.py` - Django's command-line utility for administrative tasks

## Development

### Frontend Development

The project uses Tailwind CSS with PostCSS. To watch for changes and recompile CSS:
