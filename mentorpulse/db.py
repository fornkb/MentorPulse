from functools import wraps
from time import sleep
from django.db import OperationalError, connection


def retry_database_lock(function):
    """Retry whole transactions on SQLite contention, never a broken inner transaction."""
    @wraps(function)
    def wrapped(*args, **kwargs):
        nested = connection.in_atomic_block
        for attempt in range(5):
            try:
                return function(*args, **kwargs)
            except OperationalError as error:
                if nested or connection.vendor != 'sqlite' or 'locked' not in str(error).lower() or attempt == 4:
                    raise
                sleep(0.05 * (2 ** attempt))
    return wrapped
