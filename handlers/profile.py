import os
import zlib
import base64
import mimetypes

from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import peers, local_profile, get_peer_address
from config import BROADCAST_ADDRESS, MAX_IMAGE_SIZE, settings

# ========== Color Constants ==========
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ========== Constants ==========
VALID_TYPE = "PROFILE"
REQUIRED_FIELDS = ["TYPE", "USER_ID", "DISPLAY_NAME", "STATUS"]
OPTIONAL_AVATAR_FIELDS = ["AVATAR_TYPE", "AVATAR_ENCODING", "AVATAR_DATA"]

def build_profile_message():
    msg = {
        "TYPE": "PROFILE",
        "USER_ID": local_profile["USER_ID"],
        "DISPLAY_NAME": local_profile.get("DISPLAY_NAME", ""),
        "STATUS": local_profile.get("STATUS", "")
    }

    # Optional avatar fields
    if local_profile.get("AVATAR_DATA"):
        msg.update({
            "AVATAR_TYPE": local_profile.get("AVATAR_TYPE", "image/png"),
            "AVATAR_ENCODING": local_profile.get("AVATAR_ENCODING", "base64"),
            "AVATAR_DATA": local_profile["AVATAR_DATA"]
        })

    return build_message(msg)

def compress_avatar(image_path: str):
    """
    Prepare avatar fields for an image file:
    - If file is already under MAX_IMAGE_SIZE, base64-encode without compression.
    - Otherwise, try zlib compression until within size limit.
    """
    if not os.path.isfile(image_path):
        print("⚠️ File does not exist.")
        return None

    try:
        with open(image_path, "rb") as f:
            raw_data = f.read()

        # If image is already below the max size, just base64 encode it
        if len(raw_data) <= MAX_IMAGE_SIZE:
            encoded = base64.b64encode(raw_data).decode("utf-8")
            mime_type, _ = mimetypes.guess_type(image_path)
            return {
                "AVATAR_TYPE": mime_type or "application/octet-stream",
                "AVATAR_ENCODING": "base64",
                "AVATAR_DATA": encoded
            }

        # Otherwise, try compression
        for level in range(6, 10):  # compression levels from 6 to 9
            compressed = zlib.compress(raw_data, level)
            encoded = base64.b64encode(compressed).decode("utf-8")

            if len(encoded) <= MAX_IMAGE_SIZE:
                mime_type, _ = mimetypes.guess_type(image_path)
                return {
                    "AVATAR_TYPE": mime_type or "application/octet-stream",
                    "AVATAR_ENCODING": "zlib+base64",
                    "AVATAR_DATA": encoded
                }

        print(f"⚠️ Avatar image too large to compress below {MAX_IMAGE_SIZE} bytes.")
        return None

    except Exception as e:
        print(f"⚠️ Error processing avatar: {e}")
        return None


# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "PROFILE":
        return

    ip = addr[0]
    sender_user_id = msg.get("USER_ID", "").strip()

    if not all(field in msg for field in REQUIRED_FIELDS):
        if settings["VERBOSE"]:
            # print(msg)
            print(f"{YELLOW}⚠️  Malformed PROFILE received (missing fields).{RESET}")
        return

    # Extract username from sender USER_ID and from our own local_profile
    try:
        sender_username = sender_user_id.split("@")[0].lower()
        local_username = local_profile["USER_ID"].split("@")[0].lower()
    except Exception:
        if settings["VERBOSE"]:
            # print(msg)
            print(f"{YELLOW}⚠️  Malformed USER_ID in PROFILE.{RESET}")
        return

    # Ignore if same username (regardless of IP/interface)
    if sender_username == local_username:
        if settings["VERBOSE"]:
            print(f"{BLUE}ℹ️  Ignoring self profile broadcast.{RESET}")
        return

    # Save peer info using the full USER_ID
    peers[sender_user_id] = {
        "DISPLAY_NAME": msg.get("DISPLAY_NAME", ""),
        "STATUS": msg.get("STATUS", ""),
        "ADDRESS": ip,
        "AVATAR_TYPE": msg.get("AVATAR_TYPE", ""),
        "AVATAR_ENCODING": msg.get("AVATAR_ENCODING", ""),
        "AVATAR_DATA": msg.get("AVATAR_DATA", ""),
    }

    if "AVATAR_DATA" in msg:
        peers[sender_user_id]["AVATAR_TYPE"] = msg.get("AVATAR_TYPE", "image/png")

    avatar_data = msg.get("AVATAR_DATA", "")
    avatar_preview = avatar_data[:30] + ("..." if len(avatar_data) > 30 else "")
    avatar_size = len(avatar_data.encode("utf-8"))


    if settings["VERBOSE"]:
        print(f"\n{CYAN}📥 PROFILE received from {sender_user_id}{RESET}")
        print(f"  {BLUE}TYPE:{RESET} {msg.get('TYPE', '')}")
        print(f"  {BLUE}USER_ID:{RESET} {msg.get('USER_ID', '')}")
        print(f"  {BLUE}DISPLAY_NAME:{RESET} {msg.get('DISPLAY_NAME', '')}")
        print(f"  {BLUE}STATUS:{RESET} {msg.get('STATUS', '')}")
        print(f"  {BLUE}AVATAR_TYPE:{RESET} {msg.get('AVATAR_TYPE', '')}")
        print(f"  {BLUE}AVATAR_ENCODING:{RESET} {msg.get('AVATAR_ENCODING', '')}")
        print(f"  {BLUE}AVATAR_DATA:{RESET} \"{avatar_preview}\" ({avatar_size} bytes)")
    else:
        print(f"{CYAN}👤 {msg.get('NAME', '')}:{RESET} {msg.get('STATUS', '')}")

# ========== Send ==========
def cli_send():
    name = input("Display Name: ").strip()
    avatar = input("Avatar (emoji or image path, enter to skip): ").strip()
    status = input("Status message: ").strip()
    # token = input("Optional token (press enter to skip): ").strip()

    local_profile["DISPLAY_NAME"] = name
    local_profile["STATUS"] = status

    avatar_data = None

    # Inside your cli_send() function, after user provides avatar path:
    if avatar:
        if os.path.isfile(avatar):
            try:
                avatar_data = compress_avatar(avatar)
                if isinstance(avatar_data, dict):
                    local_profile.update(avatar_data)
                else:
                    print(f"{YELLOW}⚠️ Avatar compression failed or too large. Skipping avatar.{RESET}")
            except Exception as e:
                print(f"{RED}⚠️ Failed to read avatar image: {e}{RESET}")
        else:
            # Treat as emoji string
            local_profile["AVATAR_TYPE"] = "text/emoji"
            local_profile["AVATAR_ENCODING"] = "utf-8"
            local_profile["AVATAR_DATA"] = avatar.encode("utf-8").hex()
    else:
        local_profile.pop("AVATAR_DATA", None)
        local_profile.pop("AVATAR_TYPE", None)
        local_profile.pop("AVATAR_ENCODING", None)


    message = {
        "TYPE": "PROFILE",
        "USER_ID": local_profile["USER_ID"],
        "DISPLAY_NAME": local_profile["DISPLAY_NAME"],
        "STATUS": local_profile["STATUS"],
    }

    if local_profile.get("AVATAR_DATA"):
        message.update({
            "AVATAR_TYPE": local_profile.get("AVATAR_TYPE"),
            "AVATAR_ENCODING": local_profile.get("AVATAR_ENCODING"),
            "AVATAR_DATA": local_profile.get("AVATAR_DATA"),
        })

    # if token:
    #     message["TOKEN"] = token

    send_udp(build_message(message), BROADCAST_ADDRESS)

    if settings["VERBOSE"]:
        print(f"{GREEN}✅ PROFILE broadcasted.{RESET}")
