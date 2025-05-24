from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from events.models import Event

class StaticSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return ['home', 'login', 'register']

    def location(self, item):
        return reverse(item)


class EventSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        return Event.objects.filter(is_published=True)

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return reverse('event_detail', args=[obj.id])
