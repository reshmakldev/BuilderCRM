from django.apps import AppConfig


class LeadsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leads'

    def ready(self):
        import os
        # Avoid starting the scheduler twice when Django's auto-reloader runs
        if os.environ.get('RUN_MAIN') == 'true':
            from . import scheduler
            scheduler.start()
