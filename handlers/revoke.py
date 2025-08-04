from message import build_message
from socket_handler import send_udp
from config import BROADCAST_ADDRESS
from state import revoked_tokens, tokens, local_profile

def handle(msg: dict, addr: tuple):
    token = msg.get("TOKEN")
    if token:
        revoked_tokens.add(token)
        if token in tokens:
            del tokens[token]

def send_revoke(token: str):

    message_str = build_message({
        "TYPE": "REVOKE",
        "TOKEN": token
    })

    # Send it to the broadcast address
    send_udp(message_str, BROADCAST_ADDRESS)

    # Mark as revoked locally
    revoked_tokens.add(token)
    if token in tokens:
        del tokens[token]

def revoke_all_tokens_by_user():
    user_id = local_profile["USER_ID"]
    for token in list(tokens.keys()):
        if token.startswith(user_id + "|"):
            send_revoke(token)