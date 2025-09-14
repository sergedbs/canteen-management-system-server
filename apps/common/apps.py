from django.apps import AppConfig


class CommonConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.common"

    def ready(self):
        from django.db.models.signals import post_migrate
        from django.dispatch import receiver

        from .permissions import create_default_groups

        @receiver(post_migrate)
        def create_groups(sender, **kwargs):
            create_default_groups(sender, **kwargs)
