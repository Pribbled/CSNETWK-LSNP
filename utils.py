import random
import time
import socket
import hashlib

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

def get_local_ip():
    try:
        # Connect to a public IP (Google DNS) to find the outbound interface
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"  # fallback


def current_unix_timestamp() -> int:
    return int(time.time())

def generate_message_id() -> str:
    return '%016x' % random.getrandbits(64)

def generate_token(user_id: str, ttl: int, scope: str, timestamp: int = int(time.time())) -> str:
    expiry_time = timestamp + ttl
    return f"{user_id}|{expiry_time}|{scope}"

def generate_game_id() -> str:
    return f"g{random.randint(0, 255)}"

def parse_csv(s: str) -> list:
    return [x.strip() for x in s.split(',') if x.strip()]

def hash_token(token):
    return hashlib.sha256(token.encode()).hexdigest()

def validate_token(token: str, expected_scope: str) -> bool:
    if not token or '|' not in token:
        return False

    parts = token.split('|')
    if len(parts) != 3:
        return False

    user_id, expiration, scope = parts

    # print(f"[{user_id}]\nNow: {int(time.time())}\nExp: {expiration}\nScope: {scope}")

    try:
        expiration = int(expiration)
    except ValueError:
        print(ValueError)
        return False

    current_time = int(time.time())
    if current_time > expiration:
        print(current_time, " > ", expiration)
        return False

    if scope.strip().lower() != expected_scope.lower():
        print(scope.strip().lower(), '!=', expected_scope)
        return False

    return True
