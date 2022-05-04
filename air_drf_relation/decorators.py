from django import db
from datetime import datetime


def queries_count(func):
    def inner(*args, **kwargs):
        init_count = len(db.connection.queries)
        start_time = datetime.utcnow()
        res = func(*args, **kwargs)
        end_time = datetime.utcnow()
        end_count = len(db.connection.queries)
        values = [
            datetime.utcnow().strftime("%H:%M:%S.%f"),
            f'{func.__module__}, {func.__qualname__}',
            f'count: {end_count - init_count}',
            f'range: {init_count} -> {end_count}',
            f'duration: {(end_time - start_time).total_seconds()}s.'
        ]
        print(' | '.join(values))
        return res

    return inner
