from django.core.management.base import BaseCommand
from django_q.models import OrmQ, Success, Failure


class Command(BaseCommand):
    help = 'Clear Django-Q2 task queue and optionally task history'

    def add_arguments(self, parser):
        parser.add_argument(
            '--include-history',
            action='store_true',
            help='Also clear successful and failed task history',
        )
        parser.add_argument(
            '--failures-only',
            action='store_true',
            help='Only clear failed tasks from history',
        )

    def handle(self, *args, **options):
        # Clear pending queue
        queued_count = OrmQ.objects.count()
        OrmQ.objects.all().delete()
        self.stdout.write(f"Cleared {queued_count} pending tasks from queue")

        if options['failures_only']:
            failed_count = Failure.objects.count()
            Failure.objects.all().delete()
            self.stdout.write(f"Cleared {failed_count} failed task records")
        elif options['include_history']:
            success_count = Success.objects.count()
            failed_count = Failure.objects.count()
            Success.objects.all().delete()
            Failure.objects.all().delete()
            self.stdout.write(f"Cleared {success_count} successful task records")
            self.stdout.write(f"Cleared {failed_count} failed task records")

        self.stdout.write(self.style.SUCCESS("Queue cleared successfully"))
