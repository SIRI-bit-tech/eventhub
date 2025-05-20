from django.contrib import admin
from django.utils.html import format_html
from .models import Event, RSVP, UserProfile


class RSVPInline(admin.TabularInline):
    model = RSVP
    extra = 0
    fields = ('user', 'status', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'organizer', 'start_time', 'end_time', 'location', 'is_public', 'attendee_count',
                    'is_full')
    list_filter = ('is_public', 'category', 'start_time')
    search_fields = ('title', 'description', 'location', 'organizer__username')
    date_hierarchy = 'start_time'
    readonly_fields = ('created_at', 'updated_at', 'attendee_count', 'is_full')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'organizer')
        }),
        ('Event Details', {
            'fields': ('location', 'start_time', 'end_time', 'max_attendees', 'category', 'is_public')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('created_at', 'updated_at', 'attendee_count', 'is_full')
        }),
    )
    inlines = [RSVPInline]

    def attendee_count(self, obj):
        return obj.rsvps.filter(status='attending').count()

    attendee_count.short_description = 'Attendees'


@admin.register(RSVP)
class RSVPAdmin(admin.ModelAdmin):
    list_display = ('user', 'event', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'event__title')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'location', 'profile_picture_preview')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('profile_picture_preview',)

    def display_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    display_name.short_description = 'Name'

    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                               obj.profile_picture.url)
        return "No Image"

    profile_picture_preview.short_description = 'Profile Picture'