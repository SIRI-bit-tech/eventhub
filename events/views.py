from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Event, RSVP, UserProfile
from .forms import EventForm, RSVPForm, CustomUserCreationForm, UserProfileForm, UserUpdateForm
from .serializers import EventSerializer, RSVPSerializer
from .tasks import send_event_notification, send_event_reminder
import json
from django.utils.http import urlencode
import datetime


def home(request):
    """Home page with event listings"""
    # Get search parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    location_filter = request.GET.get('location', '')

    # Show all upcoming events, regardless of is_public
    events = Event.objects.filter(
        start_time__gte=timezone.now()
    ).select_related('organizer').prefetch_related('rsvps')

    # Apply filters
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    if category_filter:
        events = events.filter(category=category_filter)

    if location_filter:
        events = events.filter(location__icontains=location_filter)

    # Order by start time
    events = events.order_by('start_time')

    # Pagination
    paginator = Paginator(events, 12)  # Show 12 events per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get categories for filter dropdown
    categories = [
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('meetup', 'Meetup'),
        ('social', 'Social'),
        ('sports', 'Sports'),
        ('arts', 'Arts & Culture'),
        ('business', 'Business'),
        ('education', 'Education'),
        ('technology', 'Technology'),
        ('health', 'Health & Wellness'),
        ('other', 'Other'),
    ]

    # Get unique locations for filter dropdown
    locations = Event.objects.values_list('location', flat=True).distinct()

    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'location_filter': location_filter,
        'categories': categories,
        'locations': locations,
    }

    return render(request, 'events/home.html', context)


def event_list_partial(request):
    """HTMX partial for event list"""
    # Get search parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    location_filter = request.GET.get('location', '')

    # Base queryset for public events
    events = Event.objects.filter(
        is_public=True,
        start_time__gte=timezone.now()
    ).select_related('organizer').prefetch_related('rsvps')

    # Apply filters
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    if category_filter:
        events = events.filter(category=category_filter)

    if location_filter:
        events = events.filter(location__icontains=location_filter)

    # Order by start time
    events = events.order_by('start_time')

    # Pagination
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'events/partials/event_list.html', {'page_obj': page_obj})


def load_events_by_category(request):
    """Load events filtered by category (for AJAX/HTMX requests)"""
    category = request.GET.get('category', '')

    events = Event.objects.filter(
        is_public=True,
        start_time__gte=timezone.now()
    )

    if category:
        events = events.filter(category=category)

    events = events.order_by('start_time')

    # Optional: paginate here if needed, or just send all results
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'events/partials/event_list.html', {'page_obj': page_obj})


def event_detail(request, pk):
    """Event detail page"""
    event = get_object_or_404(Event, pk=pk)

    # Check if user can view this event
    if not event.is_public and event.organizer != request.user:
        if not request.user.is_authenticated:
            messages.error(request, 'You need to be logged in to view this event.')
            return redirect('login')

        # Check if user is an attendee
        if not event.rsvps.filter(user=request.user, status='attending').exists():
            messages.error(request, 'You do not have permission to view this event.')
            return redirect('home')

    # Get user's RSVP status
    user_rsvp = None
    if request.user.is_authenticated:
        try:
            user_rsvp = RSVP.objects.get(event=event, user=request.user)
        except RSVP.DoesNotExist:
            pass

    # Get attendees
    attendees = event.rsvps.filter(status='attending').select_related('user')

    # RSVP form
    rsvp_form = RSVPForm()

    context = {
        'event': event,
        'user_rsvp': user_rsvp,
        'attendees': attendees,
        'rsvp_form': rsvp_form,
        'can_edit': request.user == event.organizer,
    }

    return render(request, 'events/event_detail.html', context)


@login_required
def event_create(request):
    """Create a new event"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            messages.success(request, 'Event created successfully!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm()

    return render(request, 'events/event_form.html', {'form': form, 'title': 'Create Event'})


@login_required
def event_edit(request, pk):
    """Edit an existing event"""
    event = get_object_or_404(Event, pk=pk, organizer=request.user)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', pk=event.pk)
    else:
        form = EventForm(instance=event)

    return render(request, 'events/event_form.html', {
        'form': form,
        'title': 'Edit Event',
        'event': event
    })

def about(request):
    """View for the about page"""
    return render(request, 'events/about.html')

def contact(request):
    """View for the contact page"""
    if request.method == 'POST':
        # Check if it's an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # Get form data
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')
        
        if name and email and subject and message_text:
            # Process the contact form submission
            try:
                # Email to admin
                admin_subject = f"Contact Form: {subject}"
                admin_message = f"""
                New contact form submission:
                
                Name: {name}
                Email: {email}
                Subject: {subject}
                Message:
                {message_text}
                """
                
                send_mail(
                    subject=admin_subject,
                    message=admin_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.ADMIN_EMAIL],
                    fail_silently=False,
                )
                
                # Confirmation email to user
                user_subject = "Thank you for contacting EventHub"
                user_message = f"""
                Dear {name},
                
                Thank you for contacting EventHub. We have received your message and will get back to you shortly.
                
                Your message:
                {message_text}
                
                Best regards,
                The EventHub Team
                """
                
                send_mail(
                    subject=user_subject,
                    message=user_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    fail_silently=False,
                )
                
                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'message': 'Your message has been sent. We will contact you soon!'
                    })
                else:
                    messages.success(request, 'Your message has been sent. We will contact you soon!')
            
            except Exception as e:
                if is_ajax:
                    return JsonResponse({
                        'success': False,
                        'message': 'An error occurred while sending your message. Please try again later.'
                    })
                else:
                    messages.error(request, 'An error occurred while sending your message. Please try again later.')
        else:
            if is_ajax:
                return JsonResponse({
                    'success': False,
                    'message': 'Please fill in all fields.'
                })
            else:
                messages.error(request, 'Please fill in all fields.')
    
    return render(request, 'events/contact.html')

def privacy(request):
    """View for the privacy policy page"""
    return render(request, 'events/privacy.html')

def terms(request):
    """View for the terms of service page"""
    return render(request, 'events/terms.html')


@login_required
def event_delete(request, pk):
    """Delete an event"""
    event = get_object_or_404(Event, pk=pk, organizer=request.user)

    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully!')
        return redirect('home')

    return render(request, 'events/event_confirm_delete.html', {'event': event})


@login_required
@require_http_methods(["POST"])
def rsvp_event(request, pk):
    """RSVP to an event (HTMX endpoint)"""
    event = get_object_or_404(Event, pk=pk)

    # Check if event is full
    if event.is_full:  # Changed from event.is_full()
        return JsonResponse({'error': 'Event is full'}, status=400)

    # Get or create RSVP
    rsvp, created = RSVP.objects.get_or_create(
        event=event,
        user=request.user,
        defaults={'status': 'attending'}
    )

    if not created:
        # Update existing RSVP
        new_status = request.POST.get('status', 'attending')
        rsvp.status = new_status
        rsvp.save()

    # Send notification to organizer
    if rsvp.status == 'attending':
        send_event_notification.delay(
            event.id,
            f"{request.user.get_full_name() or request.user.username} has RSVP'd to your event: {event.title}"
        )

    # Return updated RSVP button
    context = {
        'event': event,
        'user_rsvp': rsvp,
    }

    return render(request, 'events/partials/rsvp_button.html', context)


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful! Welcome to EventHub!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()

    return render(request, 'events/register.html', {'form': form})


@login_required
def add_event_to_calendar(request, pk):
    event = get_object_or_404(Event, pk=pk)
    base_url = "https://calendar.google.com/calendar/render"
    params = {
        "action": "TEMPLATE",
        "text": event.title,
        "details": event.description,
        "location": event.location,
        "dates": f"{event.start_time.strftime('%Y%m%dT%H%M%SZ')}/{event.end_time.strftime('%Y%m%dT%H%M%SZ')}",
    }
    google_calendar_url = f"{base_url}?{urlencode(params)}"
    return render(request, 'events/add_to_calendar.html', {
        'event': event,
        'google_calendar_url': google_calendar_url
    })


@login_required
def download_ics(request, pk):
    event = get_object_or_404(Event, pk=pk)
    ics_content = f"""BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//YourApp//EN\nBEGIN:VEVENT\nUID:{event.pk}@yourapp.com\nDTSTAMP:{event.start_time.strftime('%Y%m%dT%H%M%SZ')}\nDTSTART:{event.start_time.strftime('%Y%m%dT%H%M%SZ')}\nDTEND:{event.end_time.strftime('%Y%m%dT%H%M%SZ')}\nSUMMARY:{event.title}\nDESCRIPTION:{event.description}\nLOCATION:{event.location}\nEND:VEVENT\nEND:VCALENDAR\n"""
    response = HttpResponse(ics_content, content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename=event_{event.pk}.ics'
    return response


@login_required
def profile_view(request):
    """User profile view and edit"""
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)

            # Handle profile picture
            if 'profile_picture' in request.POST and request.POST['profile_picture']:
                try:
                    # Ensure the profile picture is properly saved
                    profile.profile_picture = request.POST['profile_picture']
                except Exception as e:
                    print(f"Error saving profile picture: {e}")

            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=profile)

    # Get user's events
    organized_events = Event.objects.filter(
        organizer=request.user,
        start_time__gte=timezone.now()
    ).order_by('start_time')

    attending_events = Event.objects.filter(
        rsvps__user=request.user,
        rsvps__status='attending',
        start_time__gte=timezone.now()
    ).exclude(organizer=request.user).order_by('start_time')

    past_events = Event.objects.filter(
        Q(organizer=request.user) | Q(rsvps__user=request.user, rsvps__status='attending'),
        start_time__lt=timezone.now()
    ).distinct().order_by('-start_time')

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'organized_events': organized_events,
        'attending_events': attending_events,
        'past_events': past_events,
    }

    return render(request, 'events/profile.html', context)


# API Views
class EventViewSet(viewsets.ModelViewSet):
    """API ViewSet for Events"""
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Event.objects.filter(is_public=True)

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category is not None:
            queryset = queryset.filter(category=category)

        # Filter by location
        location = self.request.query_params.get('location', None)
        if location is not None:
            queryset = queryset.filter(location__icontains=location)

        # Search
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('start_time')

    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def rsvp(self, request, pk=None):
        """RSVP to an event"""
        event = self.get_object()

        if event.is_full():
            return Response({'error': 'Event is full'}, status=400)

        rsvp, created = RSVP.objects.get_or_create(
            event=event,
            user=request.user,
            defaults={'status': 'attending'}
        )

        if not created:
            rsvp.status = request.data.get('status', 'attending')
            rsvp.save()

        serializer = RSVPSerializer(rsvp)
        return Response(serializer.data)


class RSVPViewSet(viewsets.ModelViewSet):
    """API ViewSet for RSVPs"""
    serializer_class = RSVPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RSVP.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@csrf_exempt
def google_calendar_webhook(request):
    """Webhook endpoint for Google Calendar notifications"""
    if request.method == 'POST':
        # Handle Google Calendar webhook
        # This is a placeholder for Google Calendar integration
        return HttpResponse(status=200)

    return HttpResponse(status=405)