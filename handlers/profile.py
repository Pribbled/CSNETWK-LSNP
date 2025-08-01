from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import peers, local_profile, get_peer_address
from config import BROADCAST_ADDRESS, VERBOSE
import config

# ========== Constants ==========
VALID_TYPE = "PROFILE"
REQUIRED_FIELDS = ["TYPE", "USER_ID", "NAME", "STATUS"]
OPTIONAL_AVATAR_FIELDS = ["AVATAR_TYPE", "AVATAR_ENCODING", "AVATAR_DATA"]

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "PROFILE":
        return

    ip = addr
    sender_user_id = msg.get("USER_ID", "").strip()

    if not all(field in msg for field in REQUIRED_FIELDS):
        if VERBOSE:
            print("⚠️  Malformed PROFILE received (missing fields).")
        return

    # Extract username from sender USER_ID and from our own local_profile
    try:
        sender_username = sender_user_id.split("@")[0].lower()
        local_username = local_profile["USER_ID"].split("@")[0].lower()
    except Exception:
        if VERBOSE:
            print("⚠️  Malformed USER_ID in PROFILE.")
        return

    # Ignore if same username (regardless of IP/interface)
    if sender_username == local_username:
        if VERBOSE:
            print("ℹ️  Ignoring self profile broadcast.")
        return

    # Save peer info using the full USER_ID
    peers[sender_user_id] = {
        "NAME": msg.get("NAME", ""),
        "STATUS": msg.get("STATUS", ""),
        "ADDRESS": get_peer_address(sender_user_id),
        "AVATAR_TYPE": msg.get("AVATAR_TYPE", ""),
        "AVATAR_ENCODING": msg.get("AVATAR_ENCODING", ""),
        "AVATAR_DATA": msg.get("AVATAR_DATA", ""),
    }

    if VERBOSE:
        print(f"\n📥 PROFILE received from {sender_user_id}")
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

    local_profile["NAME"] = name
    local_profile["AVATAR"] = avatar
    local_profile["STATUS"] = status

    message = {
        "TYPE": "PROFILE",
        "USER_ID": local_profile["USER_ID"],
        "NAME": name,
        "STATUS": status,
        "AVATAR_TYPE": "text/emoji",
        "AVATAR_ENCODING": "utf-8",
        "AVATAR_DATA": avatar.encode("utf-8").hex(),  # or base64 if you're using that
    }

    if token:
        message["TOKEN"] = token

    send_udp(build_message(message), BROADCAST_ADDRESS)

    if VERBOSE:
        print("✅ PROFILE broadcasted.")
