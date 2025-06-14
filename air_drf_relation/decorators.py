from datetime import datetime
from functools import wraps
from typing import Any, Callable, TypeVar

from django import db

F = TypeVar('F', bound=Callable[..., Any])


def queries_count(func: F) -> F:
    """
    Decorator that tracks database queries count and execution time for a function.

    Args:
        func: Function to be decorated

    Returns:
        Decorated function with queries tracking printed to console
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        init_count = len(db.connection.queries)
        start_time = datetime.now()

        try:
            result = func(*args, **kwargs)

            end_time = datetime.now()
            end_count = len(db.connection.queries)

            queries_executed = end_count - init_count
            duration = (end_time - start_time).total_seconds()
            timestamp = start_time.strftime('%H:%M:%S.%f')[:-3]

            function_name = f'{func.__module__}.{func.__qualname__}'

            print(
                f'[{timestamp}] {function_name} | '
                f'Queries: {queries_executed} | '
                f'Range: {init_count} → {end_count} | '
                f'Duration: {duration:.3f}s'
            )

            return result

        except Exception as e:
            end_time = datetime.now()
            end_count = len(db.connection.queries)
            queries_executed = end_count - init_count
            duration = (end_time - start_time).total_seconds()

            print(
                f'ERROR in {func.__module__}.{func.__qualname__} | '
                f'Queries before error: {queries_executed} | '
                f'Duration before error: {duration:.3f}s | '
                f'Error: {str(e)}'
            )
            raise e

    return wrapper
