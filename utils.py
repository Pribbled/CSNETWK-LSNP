import random
import time
import socket

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
    expiry_time = timestamp + ttl
    return f"{user_id}|{expiry_time}|{scope}"

def generate_game_id() -> str:
    return f"g{random.randint(0, 255)}"

def parse_csv(s: str) -> list:
    return [x.strip() for x in s.split(',') if x.strip()]

