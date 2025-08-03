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

def generate_token(user_id: str, timestamp: int, ttl: int, scope: str) -> str:
    return f"{user_id}|{str(timestamp)}+{str(ttl)}|{scope}"

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

    user_id, expiration_expr, scope = parts

    try:
        if '+' in expiration_expr:
            timestamp_str, ttl_str = expiration_expr.split('+')
            expiration = int(timestamp_str)
            ttl = int(ttl_str)
            expiration = expiration  # Already a timestamp, so nothing to add
        else:
            expiration = int(expiration_expr)
    except ValueError:
        return False

    current_time = int(time.time())
    if current_time > expiration:
        return False

    if scope.strip().lower() != expected_scope.lower():
        return False

    return True

