from message import build_message
from socket_handler import send_udp
from utils import (
    generate_message_id,
    current_unix_timestamp,
    generate_token,
)
from state import posts, local_profile, follow_map, liked_posts
from config import BROADCAST_ADDRESS, VERBOSE


def cli_send():
    print("Send a post or like: [1] POST  [2] LIKE / UNLIKE")
    choice = input("Choose type (1/2): ").strip()

    if choice == "1":
        send_post()
    elif choice == "2":
        send_like()
    else:
        print("❌ Invalid choice.")


def send_post():
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
        
    print("✅ POST broadcast sent.")


def send_like():
    post_timestamp = input("Enter TIMESTAMP of post to like/unlike: ").strip()
    action = input("Action [LIKE/UNLIKE]: ").strip().upper()

    if action not in ["LIKE", "UNLIKE"]:
        print("❌ Invalid action.")
        return

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        print("❌ Invalid TIMESTAMP.")
        return

    post = posts.get(post_timestamp)
    if not post:
        print("❌ No post found with that TIMESTAMP.")
        return

    target_user = post["USER_ID"]
    sender = local_profile["USER_ID"]
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(sender, timestamp, ttl, "broadcast")

    # Avoid duplicate likes/unlikes
    if action == "LIKE" and post_timestamp in liked_posts:
        print("⚠️ Already liked.")
        return
    elif action == "UNLIKE" and post_timestamp not in liked_posts:
        print("⚠️ Cannot unlike a post that was not liked.")
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
    print(f"✅ {action} sent to {target_user}.")


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
    timestamp = msg.get("TIMESTAMP")

    if not user or not content or not timestamp:
        if VERBOSE:
            print("⚠️ Malformed POST received.")
        return

    try:
        timestamp = int(timestamp)
    except ValueError:
        if VERBOSE:
            print("⚠️ Invalid TIMESTAMP format.")
        return

    # if user not in follow_map or local_profile["USER_ID"] not in follow_map[user]:
    #     if VERBOSE:
    #         print(f"🚫 Not following {user}. Ignoring POST.")
    #     return

    posts[timestamp] = msg
    display = user.split("@")[0]  # Use handle or fallback to user_id

    if VERBOSE:
        print(f"📝 POST from {user}: {content}")
    else:
        print(f"{display}: {content}")

def handle_like(msg: dict):
    msg_type = msg.get("TYPE", "").upper()
    if msg_type != "LIKE":
        return

    action = msg.get("ACTION", "").upper()
    from_user = msg.get("FROM", "")
    to_user = msg.get("TO", "")
    post_timestamp = msg.get("POST_TIMESTAMP", "")
    token = msg.get("TOKEN", "")

    # Basic validation
    if action not in ["LIKE", "UNLIKE"] or not from_user or not to_user or not post_timestamp:
        if VERBOSE:
            print("⚠️ Malformed LIKE/UNLIKE message.")
        return

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        if VERBOSE:
            print("⚠️ Invalid POST_TIMESTAMP format.")
        return

    # Check if the post exists
    post = posts.get(post_timestamp)
    if not post:
        if VERBOSE:
            print("⚠️ LIKE received for unknown post timestamp: ", post_timestamp)
        return

    if to_user != local_profile["USER_ID"]:
        # Message not for us
        return

    post_content = post.get("CONTENT", "")
    preview = post_content if len(post_content) <= 30 else post_content[:30] + "..."

    if VERBOSE:
        print(f"🔔 {from_user} {action.lower()}d your post [{preview}]")
    else:
        print(f"{from_user.split('@')[0]} {action.lower()}s your post [{preview}]")
