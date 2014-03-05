import re
import asyncio

class TerminalColors:
    LIGHTBLUE = '\033[96m'
    PURPLE = '\033[95m'
    DARKBLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    NORMAL = '\033[0m'
    WHITE = NORMAL + '\033[1m'


class RainfallException(Exception):
    pass


class NotModified(RainfallException):
    pass


def match_dict_regexp(d, r):
    """
    The same as d[r] but uses regex match.

    Return (d[r] and match_result)
    Return None in case no match found.
    """
    for pattern, elem in d.items():
        result = re.match(pattern, r)
        if result:
            return elem, result
    return None


def maybe_yield(f, *args, **kwargs):
    """
    Yield from if f is coroutine or call it otherwise.

    useage: a = yield from maybe_yield(f)
    """
    if asyncio.tasks.iscoroutinefunction(f):
        res = yield from f(*args, **kwargs)
        return res
    else:
        return f(*args, **kwargs)