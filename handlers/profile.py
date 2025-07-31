from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import peers, local_profile
from config import BROADCAST_ADDRESS
import config

# ========== Constants ==========
VALID_TYPE = "PROFILE"
REQUIRED_FIELDS = ["TYPE", "USER_ID", "DISPLAY_NAME", "STATUS"]
OPTIONAL_AVATAR_FIELDS = ["AVATAR_TYPE", "AVATAR_ENCODING", "AVATAR_DATA"]

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "PROFILE":
        return

    ip = addr[0]  # actual sender IP
    sender_user_id = msg.get("USER_ID", "")

    try:
        username_part = sender_user_id.split("@")[0]
    except IndexError:
        if config.VERBOSE:
            print("⚠️  Malformed USER_ID in PROFILE.")
        return

    reconstructed_user_id = f"{username_part}@{ip}"

    if reconstructed_user_id == local_profile["USER_ID"]:
        if config.VERBOSE:
            print("ℹ️  Ignoring self profile broadcast.")
        return

    # store peer info using reconstructed ID
    peers[reconstructed_user_id] = {
        "NAME": msg.get("NAME", ""),
        "STATUS": msg.get("STATUS", ""),
        "ADDRESS": ip,
        "AVATAR_TYPE": msg.get("AVATAR_TYPE", ""),
        "AVATAR_ENCODING": msg.get("AVATAR_ENCODING", ""),
        "AVATAR_DATA": msg.get("AVATAR_DATA", ""),
    }

    if config.VERBOSE:
        print(f"\n📥 PROFILE received from {reconstructed_user_id}")
        print(f"  NAME: {msg.get('NAME', '')}")
        print(f"  STATUS: {msg.get('STATUS', '')}")
        print(f"  AVATAR_TYPE: {msg.get('AVATAR_TYPE', '')}")
        print(f"  AVATAR_ENCODING: {msg.get('AVATAR_ENCODING', '')}")
        print(f"  AVATAR_DATA: (base64 {len(msg.get('AVATAR_DATA', ''))} bytes)")


# ========== Send ==========
def cli_send():
    name = input("Display Name: ").strip()
    avatar = input("Avatar (emoji): ").strip()
    status = input("Status message: ").strip()
    token = input("Optional token (press enter to skip): ").strip()

    fields = {
        "TYPE": "PROFILE",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER_ID": local_profile["USER_ID"],
        "DISPLAY_NAME": name,
        "STATUS": status,
        "TTL": str(config.DEFAULT_TTL),
    }

    # Optional avatar fields
    if avatar:
        fields["AVATAR_TYPE"] = "text/emoji"
        fields["AVATAR_ENCODING"] = "utf-8"
        fields["AVATAR_DATA"] = avatar

    if token:
        fields["TOKEN"] = token

    msg = build_message(fields)
    send_udp(msg, BROADCAST_ADDRESS)
    print("✅ PROFILE broadcasted.")