from django.apps import AppConfig

class ExcelThingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'excel_thing'

    def ready(self):
        # Make sure there are no infinite loops or unhandled blocking calls here
        pass