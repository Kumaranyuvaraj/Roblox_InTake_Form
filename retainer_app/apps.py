from django.apps import AppConfig


class RetainerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'retainer_app'
    verbose_name = 'Retainer Document Management'
    
    def ready(self):
        # Import signals if needed
        pass
