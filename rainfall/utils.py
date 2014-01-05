

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