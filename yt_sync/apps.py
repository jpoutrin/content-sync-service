from django.apps import AppConfig


class YtSyncConfig(AppConfig):
    name = "yt_sync"

    def ready(self) -> None:
        """Import signal handlers when app is ready.

        This method is called by Django when the application is ready.
        We import signals here to ensure they are registered properly.
        """
        # Import signals to register handlers
        import yt_sync.signals  # noqa: F401
