from state import revoked_tokens
from config import settings

def handle(msg: dict, addr: tuple):
    token = msg.get("TOKEN")
    if token:
        revoked_tokens.add(token)
        if settings["VERBOSE"]:
            print(f"🔒 Token revoked: {token}")
