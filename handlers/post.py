from message import build_message
from socket_handler import send_udp
from utils import generate_message_id, current_unix_timestamp
from state import posts
from config import BROADCAST_ADDRESS
import config

def cli_send():
    print("Send a post type: [1] POST  [2] REPOST  [3] LIKE")
    choice = input("Choose type (1/2/3): ").strip()

    if choice == "1":
        send_post()
    elif choice == "2":
        send_repost()
    elif choice == "3":
        send_like()
    else:
        print("❌ Invalid choice.")

def send_post():
    user = input("Your USER ID: ").strip()
    content = input("Post content: ").strip()

    fields = {
        "TYPE": "POST",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": user,
        "CONTENT": content
    }

    msg = build_message(fields)
    send_udp(msg, BROADCAST_ADDRESS)
    print("✅ POST sent.")

def send_repost():
    user = input("Your USER ID: ").strip()
    post_id = input("Original POST_ID to repost: ").strip()

    if post_id not in posts:
        print("❌ That post ID is not known locally.")
        return

    fields = {
        "TYPE": "REPOST",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": user,
        "POST_ID": post_id
    }

    msg = build_message(fields)
    send_udp(msg, BROADCAST_ADDRESS)
    print("🔁 REPOST sent.")

def send_like():
    user = input("Your USER ID: ").strip()
    post_id = input("POST_ID to like: ").strip()

    if post_id not in posts:
        print("❌ That post ID is not known locally.")
        return

    fields = {
        "TYPE": "LIKE",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": user,
        "POST_ID": post_id
    }

    msg = build_message(fields)
    send_udp(msg, BROADCAST_ADDRESS)
    print("❤️ LIKE sent.")


# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    if msg_type not in ["POST", "REPOST", "LIKE"]:
        return

    if msg_type == "POST":
        handle_post(msg, addr)
    elif msg_type == "REPOST":
        handle_repost(msg, addr)
    elif msg_type == "LIKE":
        handle_like(msg, addr)

def handle_post(msg: dict, addr: tuple):
    post_id = msg.get("ID")
    user = msg.get("USER")
    content = msg.get("CONTENT")

    if not post_id or not user or not content:
        if config.VERBOSE:
            print("⚠️  Malformed POST")
        return

    posts[post_id] = msg

    if config.VERBOSE:
        print(f"📝 POST from {user}: {content}")

def handle_repost(msg: dict, addr: tuple):
    user = msg.get("USER")
    original_id = msg.get("POST_ID")

    if not original_id or original_id not in posts:
        if config.VERBOSE:
            print("⚠️  Unknown POST_ID for REPOST")
        return

    original = posts[original_id]
    print(f"🔁 {user} reposted from {original.get('USER')}: {original.get('CONTENT')}")

def handle_like(msg: dict, addr: tuple):
    user = msg.get("USER")
    liked_id = msg.get("POST_ID")

    if not liked_id or liked_id not in posts:
        if config.VERBOSE:
            print("⚠️  Unknown POST_ID for LIKE")
        return

    original = posts[liked_id]
    print(f"❤️ {user} liked {original.get('USER')}'s post: {original.get('CONTENT')}")
