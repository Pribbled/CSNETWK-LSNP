import time
from message import build_message
from socket_handler import send_udp
from utils import (
    generate_message_id,
    current_unix_timestamp,
    generate_token,
)
from state import posts, local_profile, follow_map, liked_posts, peers
from config import BROADCAST_ADDRESS, settings

# ========== Colors ==========
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"

def cli_send():
    content = input("Post content: ").strip()
    ttl = input("TTL in seconds (default 3600): ").strip()
    ttl = int(ttl) if ttl.isdigit() else 3600

    user_id = local_profile["USER_ID"]
    timestamp = current_unix_timestamp()
    token = generate_token(user_id, timestamp, ttl, "broadcast")

    message = {
        "TYPE": "POST",
        "USER_ID": user_id,
        "CONTENT": content,
        "TTL": str(ttl),
        "TIMESTAMP": str(timestamp),
        "MESSAGE_ID": generate_message_id(),
        "TOKEN": token,
    }

    send_udp(build_message(message), BROADCAST_ADDRESS)

    posts[timestamp] = {
        "message": message,
        "from": local_profile["USER_ID"],
        "timestamp": timestamp
    }

    print(f"{GREEN}✅ POST broadcast sent.{RESET}")


def send_like():
    post_timestamp = input("Enter TIMESTAMP of post to like/unlike: ").strip()
    action = input("Action [LIKE/UNLIKE]: ").strip().upper()

    if action not in ["LIKE", "UNLIKE"]:
        print(f"{RED}❌ Invalid action.{RESET}")
        return

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        print(f"{RED}❌ Invalid TIMESTAMP.{RESET}")
        return

    post = posts.get(post_timestamp)
    if not post:
        print(f"{RED}❌ No post found with that TIMESTAMP.{RESET}")
        return

    target_user = post["USER_ID"]
    sender = local_profile["USER_ID"]
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(sender, timestamp, ttl, "broadcast")

    if action == "LIKE" and post_timestamp in liked_posts:
        print(f"{YELLOW}⚠️ Already liked.{RESET}")
        return
    elif action == "UNLIKE" and post_timestamp not in liked_posts:
        print(f"{YELLOW}⚠️ Cannot unlike a post that was not liked.{RESET}")
        return

    if action == "LIKE":
        liked_posts.add(post_timestamp)
    else:
        liked_posts.discard(post_timestamp)

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


# ===================== RECEIVE =====================

def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    if msg_type == "POST":
        handle_post(msg)
    elif msg_type == "LIKE":
        handle_like(msg)


def handle_post(msg: dict):
    user = msg.get("USER_ID")
    content = msg.get("CONTENT")
    ttl = msg.get("TTL")
    message_id = msg.get("MESSAGE_ID")
    token = msg.get("TOKEN")

    # Inject timestamp at time of receipt
    timestamp = int(time.time())

    if not user or not content: #or not timestamp
        if settings["VERBOSE"]:
            print(user)
            print(content)
            print(f"{YELLOW}⚠️ Malformed POST received.{RESET}")
        return

    try:
        timestamp = int(timestamp)
    except ValueError:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ Invalid TIMESTAMP format.{RESET}")
        return

    posts[message_id] = {
        "USER_ID": user,
        "CONTENT": content,
        "TTL": int(ttl),
        "TIMESTAMP": timestamp,
        "TOKEN": token,
    }
    display = user.split("@")[0]
 # Print post
    name = peers.get(user, {}).get("DISPLAY_NAME", user)
    avatar = peers.get(user, {}).get("AVATAR", "")

    if settings["VERBOSE"]:
        print(f"\n{BLUE}[POST]{RESET} From: {user}")
        print(f"{CYAN}DISPLAY_NAME:{RESET} {name}")
        print(f"{CYAN}CONTENT:{RESET} {content}")
        print(f"{CYAN}TTL:{RESET} {ttl}")
        print(f"{CYAN}MESSAGE_ID:{RESET} {message_id}")
        print(f"{CYAN}TOKEN:{RESET} {token}")
        print(f"{CYAN}TIMESTAMP (injected):{RESET} {timestamp}")
    else:
        display = f"{name}: {content}"
        print(f"{avatar} {display}" if avatar else display)


def handle_like(msg: dict):
    msg_type = msg.get("TYPE", "").upper()
    if msg_type != "LIKE":
        return

    action = msg.get("ACTION", "").upper()
    from_user = msg.get("FROM", "")
    to_user = msg.get("TO", "")
    post_timestamp = msg.get("POST_TIMESTAMP", "")
    token = msg.get("TOKEN", "")

    if action not in ["LIKE", "UNLIKE"] or not from_user or not to_user or not post_timestamp:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ Malformed LIKE/UNLIKE message.{RESET}")
        return

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ Invalid POST_TIMESTAMP format.{RESET}")
        return

    post = posts.get(post_timestamp)
    if not post:
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ LIKE received for unknown post timestamp: {post_timestamp}{RESET}")
        return

    if to_user != local_profile["USER_ID"]:
        return

    post_content = post.get("CONTENT", "")
    preview = post_content if len(post_content) <= 30 else post_content[:30] + "..."

    if settings["VERBOSE"]:
        print(post)
        print(f"{MAGENTA}🔔 {from_user} {action.lower()}d your post [{preview}]{RESET}")
    else:
        print(f"{MAGENTA}{from_user.split('@')[0]} {action.lower()}s your post [{preview}]{RESET}")
