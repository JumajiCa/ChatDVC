
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

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

class EncryptionManager:
    def __init__(self, key=None):
        if key:
            self.key = key
        else:
            # Try to load from env
            self.key = os.getenv("ENCRYPTION_KEY")
            
        if not self.key:
            # Check if a key file exists to maintain persistence
            key_file = "encryption.key"
            if os.path.exists(key_file):
                with open(key_file, "r") as f:
                    self.key = f.read().strip()
            else:
                print(f"{Color.YELLOW}Warning: ENCRYPTION_KEY not found. Generating and saving to {key_file} for persistence.{Color.RESET}")
                self.key = Fernet.generate_key().decode()
                try:
                    with open(key_file, "w") as f:
                        f.write(self.key)
                except IOError as e:
                     print(f"{Color.RED}Error saving encryption key: {e}{Color.RESET}")

        self.cipher_suite = Fernet(self.key.encode() if isinstance(self.key, str) else self.key)

    def encrypt(self, data: str) -> str:
        if not data:
            return ""
        return self.cipher_suite.encrypt(data.encode()).decode()

    def decrypt(self, data: str) -> str:
        if not data:
            return ""
        try:
            return self.cipher_suite.decrypt(data.encode()).decode()
        except Exception as e:
            error_handling.print_error(f"Decryption failed: {e}")
            return ""
