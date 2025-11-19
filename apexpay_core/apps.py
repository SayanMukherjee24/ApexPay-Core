from django.apps import AppConfig

class ApexpayCoreConfig(AppConfig):
    name = "apexpay_core"

    def ready(self):
        import apexpay_core.signals
