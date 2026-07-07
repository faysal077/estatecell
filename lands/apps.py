from django.apps import AppConfig


class LandsConfig(AppConfig):

    default_auto_field = 'django.db.models.BigAutoField'

    name = 'lands'

    def ready(self):

        import lands.signals