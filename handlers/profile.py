from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import peers, local_profile, get_peer_address
from config import BROADCAST_ADDRESS, settings

# ========== Color Constants ==========
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ========== Constants ==========
VALID_TYPE = "PROFILE"
REQUIRED_FIELDS = ["TYPE", "USER_ID", "NAME", "STATUS"]
OPTIONAL_AVATAR_FIELDS = ["AVATAR_TYPE", "AVATAR_ENCODING", "AVATAR_DATA"]

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "PROFILE":
        return

    ip = addr[0]
    sender_user_id = msg.get("USER_ID", "").strip()

    if not all(field in msg for field in REQUIRED_FIELDS):
        # print(msg)
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️  Malformed PROFILE received (missing fields).{RESET}")
        return

    # Extract username from sender USER_ID and from our own local_profile
    try:
        sender_username = sender_user_id.split("@")[0].lower()
        local_username = local_profile["USER_ID"].split("@")[0].lower()
    except Exception:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️  Malformed USER_ID in PROFILE.{RESET}")
        return

    # Ignore if same username (regardless of IP/interface)
    if sender_username == local_username:
        if settings["VERBOSE"]:
            print(f"{BLUE}ℹ️  Ignoring self profile broadcast.{RESET}")
        return

    # Save peer info using the full USER_ID
    peers[sender_user_id] = {
        "NAME": msg.get("NAME", ""),
        "STATUS": msg.get("STATUS", ""),
        "ADDRESS": ip,
        "AVATAR_TYPE": msg.get("AVATAR_TYPE", ""),
        "AVATAR_ENCODING": msg.get("AVATAR_ENCODING", ""),
        "AVATAR_DATA": msg.get("AVATAR_DATA", ""),
    }

    if settings["VERBOSE"]:
        print(f"\n{CYAN}📥 PROFILE received from {sender_user_id}{RESET}")
        print(f"  {BLUE}NAME:{RESET} {msg.get('NAME', '')}")
        print(f"  {BLUE}STATUS:{RESET} {msg.get('STATUS', '')}")
        print(f"  {BLUE}AVATAR_TYPE:{RESET} {msg.get('AVATAR_TYPE', '')}")
        print(f"  {BLUE}AVATAR_ENCODING:{RESET} {msg.get('AVATAR_ENCODING', '')}")
        print(f"  {BLUE}AVATAR_DATA:{RESET} (base64 {len(msg.get('AVATAR_DATA', ''))} bytes)")
    else:
        print(f"{CYAN}👤 {msg.get('NAME', '')}:{RESET} {msg.get('STATUS', '')}")

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
        "AVATAR_DATA": avatar.encode("utf-8").hex(),
    }

    if token:
        message["TOKEN"] = token

    send_udp(build_message(message), BROADCAST_ADDRESS)

    if settings["VERBOSE"]:
        print(f"{GREEN}✅ PROFILE broadcasted.{RESET}")
