from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a UserProfile for each new User if it doesn't already exist
    """
    if created:
        # Check if a profile already exists before creating a new one
        if not hasattr(instance, 'profile'):
            try:
                UserProfile.objects.create(user=instance)
                logger.info(f"Created profile for user: {instance.username}")
            except Exception as e:
                logger.error(f"Error creating profile for {instance.username}: {str(e)}")