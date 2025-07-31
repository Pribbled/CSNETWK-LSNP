from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import peers
from config import BROADCAST_ADDRESS
import config

import time

# ========== Constants ==========
REQUIRED_FIELDS = ["TYPE", "USER", "NAME"]
OPTIONAL_FIELDS = ["AVATAR", "STATUS", "TOKEN", "TTL"]
VALID_TYPE = "PROFILE"

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != VALID_TYPE:
        return

    user_id = msg.get("USER")
    name = msg.get("NAME", "")
    avatar = msg.get("AVATAR", "")
    status = msg.get("STATUS", "")
    token = msg.get("TOKEN", None)
    ttl = int(msg.get("TTL", config.DEFAULT_TTL))
    
    if not user_id:
        if config.VERBOSE:
            print(f"⚠️  PROFILE missing USER field from {addr}")
        return

    peers[user_id] = {
        "NAME": name,
        "AVATAR": avatar,
        "STATUS": status,
        "ADDRESS": addr[0],
        "TOKEN": token,
        "EXPIRES_AT": current_unix_timestamp() + ttl
    }

    if config.VERBOSE:
        print(f"👤 PROFILE received from {user_id} ({name})")

# ========== Send ==========
def cli_send():
    user_id = input("Your USER ID: ").strip()
    name = input("Display Name: ").strip()
    avatar = input("Avatar (emoji): ").strip()
    status = input("Status message: ").strip()
    token = input("Optional token (press enter to skip): ").strip()

    fields = {
        "TYPE": "PROFILE",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": user_id,
        "NAME": name
    }

    if avatar:
        fields["AVATAR"] = avatar
    if status:
        fields["STATUS"] = status
    if token:
        fields["TOKEN"] = token
    fields["TTL"] = str(config.DEFAULT_TTL)

    msg = build_message(fields)
    send_udp(msg, BROADCAST_ADDRESS)
    print("✅ PROFILE broadcasted.")
