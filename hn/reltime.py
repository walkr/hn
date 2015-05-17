# A module for transforming timestamps to relative time

import time
from collections import OrderedDict


durations = OrderedDict([
    ('second',  1.0),
    ('minute',  60.0),
    ('hour',    3600.0),
    ('day',     3600.0 * 24),
    ('week',    3600.0 * 24 * 7),
    ('month',   3600.0 * 24 * 30),
    ('year',    3600.0 * 24 * 356),
])


def _since_now(timestamp):
    now = int(time.time())
    diff = now - timestamp
    chosen_unit = None
    for unit, duration in reversed(list(durations.items())):
        if diff < duration:
            continue
        else:
            chosen_unit = unit
            break
    value = round(diff/duration, 2)
    return value, chosen_unit


def since_now(timestamp, roundoff=True):
    """ Return the diff from since timestamp to now as relative time.
    `roundoff=True` round the numerical value to nearest integer. also return
    return second in a approximate format (a few seconds ago) """

    value, unit = _since_now(timestamp)

    if roundoff:
        value = int(round(value))
        if unit in ('second', 'seconds'):
            return 'a few seconds'
        elif value > 1:
            unit += 's'
    else:
        if value > 1.0:
            unit += 's'

    return '{} {}'.format(value, unit)
