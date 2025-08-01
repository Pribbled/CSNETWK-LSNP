from message import build_message
from socket_handler import send_udp
from utils import current_unix_timestamp, generate_token
from state import posts, local_profile, liked_posts
from config import BROADCAST_ADDRESS, settings

# ========== Color Constants ==========
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

def cli_send():
    post_timestamp = input("Enter TIMESTAMP of post to like/unlike: ").strip()

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        print(f"{RED}❌ Invalid TIMESTAMP.{RESET}")
        return

    post = posts.get(post_timestamp)
    if not post:
        print(f"{RED}❌ No post found with that TIMESTAMP.{RESET}")
        return

    target_user = post.get("USER_ID")
    sender = local_profile["USER_ID"]
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(sender, timestamp, ttl, "broadcast")

    if post_timestamp in liked_posts:
        action = "UNLIKE"
        liked_posts.discard(post_timestamp)
    else:
        action = "LIKE"
        liked_posts.add(post_timestamp)

    message = {
        "TYPE": "LIKE",
        "FROM": sender,
        "TO": target_user,
        "POST_TIMESTAMP": str(post_timestamp),
        "ACTION": action,
        "TIMESTAMP": str(timestamp),
        "TOKEN": token,
    }

    send_udp(build_message(message), BROADCAST_ADDRESS)
    print(f"{GREEN}✅ {action} sent to {target_user}.{RESET}")


def handle(msg: dict, addr: tuple):
    action = msg.get("ACTION", "").upper()
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    post_timestamp = msg.get("POST_TIMESTAMP")

    if action not in ["LIKE", "UNLIKE"] or not from_user or not to_user or not post_timestamp:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ Malformed LIKE/UNLIKE message.{RESET}")
        return

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ Invalid POST_TIMESTAMP.{RESET}")
        return

    post = posts.get(post_timestamp)
    if not post:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ LIKE received for unknown post timestamp: {post_timestamp}{RESET}")
        return

    if to_user != local_profile["USER_ID"]:
        return  # likes not for us

    preview = post.get("CONTENT", post.get("message", ""))[:30]

    if settings["VERBOSE"]:
        print(f"{CYAN}💬 {action} received from {from_user} on post {post_timestamp}{RESET}")
    elif action == "LIKE":
        print(f"{GREEN}{from_user.split('@')[0]} likes your post [{preview}]{RESET}")
    elif action == "UNLIKE":
        print(f"{RED}{from_user.split('@')[0]} unliked your post [{preview}]{RESET}")
