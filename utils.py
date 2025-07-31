import random
import time

def current_unix_timestamp() -> int:
    return int(time.time())

def generate_message_id() -> str:
    return '%016x' % random.getrandbits(64)

def generate_game_id() -> str:
    return f"g{random.randint(0, 255)}"

def parse_csv(s: str) -> list:
    return [x.strip() for x in s.split(',') if x.strip()]
