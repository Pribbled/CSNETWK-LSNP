from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import peers
from config import BROADCAST_ADDRESS
import config

# ========== Constants ==========
VALID_TYPE = "PROFILE"
REQUIRED_FIELDS = ["TYPE", "USER_ID", "DISPLAY_NAME", "STATUS"]
OPTIONAL_AVATAR_FIELDS = ["AVATAR_TYPE", "AVATAR_ENCODING", "AVATAR_DATA"]

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != VALID_TYPE:
        return

    user_id = msg.get("USER_ID")
    name = msg.get("DISPLAY_NAME", "")
    status = msg.get("STATUS", "")
    avatar_type = msg.get("AVATAR_TYPE", None)
    avatar_encoding = msg.get("AVATAR_ENCODING", None)
    avatar_data = msg.get("AVATAR_DATA", None)

    if not user_id:
        if config.VERBOSE:
            print(f"⚠️  PROFILE missing USER_ID field from {addr}")
        return

    # Store or update peer info
    peers[user_id] = {
        "DISPLAY_NAME": name,
        "STATUS": status,
        "AVATAR_TYPE": avatar_type,
        "AVATAR_ENCODING": avatar_encoding,
        "AVATAR_DATA": avatar_data,
        "ADDRESS": addr[0],
        "LAST_SEEN": current_unix_timestamp()
    }

    # Output
    if config.VERBOSE:
        print(f"\n📥 PROFILE received from {user_id}")
        print(f"  NAME: {name}")
        print(f"  STATUS: {status}")
        if avatar_type and avatar_encoding and avatar_data:
            print(f"  AVATAR_TYPE: {avatar_type}")
            print(f"  AVATAR_ENCODING: {avatar_encoding}")
            print(f"  AVATAR_DATA: (base64 {len(avatar_data)} bytes)")
    else:
        print(f"{name}: {status}")

# ========== Send ==========
def cli_send():
    ip = config.LOCAL_IP if hasattr(config, 'LOCAL_IP') else "0.0.0.0"
    username = input("Username (for USER_ID): ").strip()
    user_id = f"{username}@{ip}"
    name = input("Display Name: ").strip()
    status = input("Status message: ").strip()

    # Optional avatar inputs
    avatar_type = input("Avatar MIME type (optional): ").strip()
    avatar_encoding = input("Avatar encoding (default base64): ").strip() or "base64"
    avatar_data = input("Avatar image (base64-encoded, optional): ").strip()

    fields = {
        "TYPE": VALID_TYPE,
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER_ID": user_id,
        "DISPLAY_NAME": name,
        "STATUS": status,
    }

    if avatar_type:
        fields["AVATAR_TYPE"] = avatar_type
    if avatar_encoding:
        fields["AVATAR_ENCODING"] = avatar_encoding
    if avatar_data:
        fields["AVATAR_DATA"] = avatar_data

    msg = build_message(fields)
    send_udp(msg, BROADCAST_ADDRESS)
    print("✅ PROFILE broadcasted.")
