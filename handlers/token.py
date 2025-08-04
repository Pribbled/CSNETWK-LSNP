import time
from message import build_message
from socket_handler import send_unicast, send_udp
from utils import generate_message_id, current_unix_timestamp
from state import tokens, revoked_tokens, peers, local_profile
from config import BROADCAST_ADDRESS, PORT

# Constants
DEFAULT_SCOPE = "POST,DM,FILE"
DEFAULT_EXPIRY = 3600  # 1 hour

# ========== Incoming Handler ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()

    if msg_type == "TOKEN_REPLY":
        handle_token_reply(msg)
    elif msg_type == "REVOKE":
        handle_revoke(msg)

# ========== Token Reply ==========
def handle_token_reply(msg: dict):
    token = msg.get("TOKEN")
    scope = msg.get("SCOPE", DEFAULT_SCOPE)
    expiry = int(msg.get("EXPIRY", current_unix_timestamp() + DEFAULT_EXPIRY))
    issuer = msg.get("USER")
    recipient = msg.get("TO")

    if recipient != local_profile.USER_ID or not token:
        return

    tokens[token] = {
        "USER": recipient,
        "ISSUER": issuer,
        "SCOPE": scope,
        "ISSUED_AT": current_unix_timestamp(),
        "EXPIRES_AT": expiry
    }

    print(f"✅ TOKEN_RECEIVED from {issuer} (expires in {expiry - current_unix_timestamp()}s)")

# ========== Revoke Token ==========
def handle_revoke(msg: dict, addr: tuple = None):
    token = msg.get("TOKEN")
    if not token:
        return
    revoked_tokens.add(token)
    if token in tokens:
        del tokens[token]
    # Per RFC: DO NOT print anything in non-verbose mode

# ========== Broadcast Revoke ==========
def revoke_all_tokens_by_user(user_id: str):
    for token in list(tokens.keys()):
        if token.startswith(f"{user_id}|"):
            revoke_token(token)
            revoked_tokens.add(token)
            del tokens[token]

def send_revoke_for_all_tokens(sock):
    user_id = local_profile["USER_ID"]
    for token in list(tokens.keys()):
        if token.startswith(user_id):
            revoke_msg = f"TYPE: REVOKE\nTOKEN: {token}"
            send_udp(revoke_msg, BROADCAST_ADDRESS, PORT)
            del tokens[token]  # Remove locally too

def revoke_token(token: str):
    msg = build_message({
        "TYPE": "REVOKE",
        "TOKEN": token
    })
    send_udp(msg, BROADCAST_ADDRESS, PORT)
