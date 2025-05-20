from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q

from .models import Event, RSVP, UserProfile
from .forms import EventForm, RSVPForm, CustomUserCreationForm, UserProfileForm, UserUpdateForm


class HomeView(ListView):
    model = Event
    template_name = 'events/home.html'
    context_object_name = 'events'
    paginate_by = 9

    def get_queryset(self):
        queryset = Event.objects.filter(
            is_public=True,
            end_time__gte=timezone.now()
        ).order_by('start_time')

        # Filter by search query if provided
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(location__icontains=query) |
                Q(category__icontains=query)
            )

        # Filter by category if provided
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Event.objects.values_list('category', flat=True).distinct()
        context['now'] = timezone.now()
        return context


class EventDetailView(DetailView):
    model = Event
    template_name = 'events/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['rsvp_form'] = RSVPForm()
            try:
                context['user_rsvp'] = RSVP.objects.get(user=self.request.user, event=self.object)
            except RSVP.DoesNotExist:
                context['user_rsvp'] = None

        context['attendees'] = self.object.rsvps.filter(status='attending')
        return context


class EventCreateView(LoginRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)


class EventUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'events/event_form.html'

    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer

    def form_valid(self, form):
        form.instance.organizer = self.request.user
        return super().form_valid(form)


class EventDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Event
    template_name = 'events/event_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        event = self.get_object()
        return self.request.user == event.organizer


@login_required
def rsvp_event(request, pk):
    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST' and request.htmx:
        try:
            rsvp = RSVP.objects.get(user=request.user, event=event)
            form = RSVPForm(request.POST, instance=rsvp)
        except RSVP.DoesNotExist:
            form = RSVPForm(request.POST)

        if form.is_valid():
            rsvp = form.save(commit=False)
            rsvp.user = request.user
            rsvp.event = event

            # Check if event is full
            if rsvp.status == 'attending' and event.is_full:
                messages.error(request, "This event is already full.")
                return HttpResponse(
                    '<div class="text-red-500">Event is full</div>',
                    headers={'HX-Trigger': 'showMessage'}
                )

            rsvp.save()

            # Return HTMX response
            context = {
                'event': event,
                'user_rsvp': rsvp,
                'rsvp_form': RSVPForm(instance=rsvp),
            }
            return render(request, 'events/partials/rsvp_form.html', context)

    return redirect('event_detail', pk=pk)


@login_required
def profile_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)

    # Get user's events
    organized_events = Event.objects.filter(organizer=request.user)
    attending_events = Event.objects.filter(
        rsvps__user=request.user,
        rsvps__status='attending',
        end_time__gte=timezone.now()
    )
    past_events = Event.objects.filter(
        rsvps__user=request.user,
        rsvps__status='attending',
        end_time__lt=timezone.now()
    )

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'organized_events': organized_events,
        'attending_events': attending_events,
        'past_events': past_events,
    }

    return render(request, 'events/profile.html', context)


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Fix: Changed from request.POSTister to request.POST
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()

    return render(request, 'events/register.html', {'form': form})


# HTMX Views
@login_required
def load_events_by_category(request):
    category = request.GET.get('category')
    if category:
        events = Event.objects.filter(
            category=category,
            is_public=True,
            end_time__gte=timezone.now()
        ).order_by('start_time')
    else:
        events = Event.objects.filter(
            is_public=True,
            end_time__gte=timezone.now()
        ).order_by('start_time')

    return render(request, 'events/partials/event_list.html', {'events': events})


@login_required
def toggle_attendance(request, pk):
    event = get_object_or_404(Event, pk=pk)

    try:
        rsvp = RSVP.objects.get(user=request.user, event=event)
        if rsvp.status == 'attending':
            rsvp.status = 'declined'
        else:
            rsvp.status = 'attending'
        rsvp.save()
    except RSVP.DoesNotExist:
        if not event.is_full:
            RSVP.objects.create(
                user=request.user,
                event=event,
                status='attending'
            )

    # Return updated button
    context = {
        'event': event,
        'user_rsvp': RSVP.objects.get(user=request.user, event=event)
    }
    return render(request, 'events/partials/attendance_button.html', context)