import logging
from threading import Event, Thread
from django.core.management import call_command
from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand
from django.db import close_old_connections


class Command(RunserverCommand):
    help = 'Run the local development server with automatic session reminders every minute.'

    def inner_run(self, *args, **options):
        stop = Event()
        def worker():
            while not stop.is_set():
                try:
                    close_old_connections()
                    call_command('send_session_reminders', stdout=self.stdout)
                except Exception:
                    logging.getLogger(__name__).exception('Session reminder worker failed; retrying next minute')
                finally:
                    close_old_connections()
                stop.wait(60)
        thread = Thread(target=worker, name='session-reminders', daemon=True)
        thread.start()
        try:
            super().inner_run(*args, **options)
        finally:
            stop.set()
            thread.join(timeout=1)
