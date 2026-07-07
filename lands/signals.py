from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Land
from .models import LandVerification


@receiver(post_save, sender=Land)
def create_verification(sender, instance, created, **kwargs):

    if created:

        LandVerification.objects.create(
            land=instance
        )