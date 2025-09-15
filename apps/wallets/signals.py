from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.wallets.models import Balance


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_balance(sender, instance, created, **kwargs):
    if created:
        Balance.objects.create(user=instance)
