
class Color: 
    # ANSI escape codes for standard colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    # ANSI escape code to reset to default terminal color/style
    RESET = '\033[0m'
    # Other styles, e.g., bold
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class error_handling: 
    # def __init__(self): 
    #    self.error_buffer = []
    @staticmethod
    def print_error(error_text: str): 
        print(f"{Color.RED}{error_text}{Color.RESET}\n")