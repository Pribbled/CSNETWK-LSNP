from message import build_message
from socket_handler import send_udp
from utils import current_unix_timestamp, generate_token
from state import posts, local_profile, liked_posts
from config import BROADCAST_ADDRESS, VERBOSE

def cli_send():
    post_timestamp = input("Enter TIMESTAMP of post to like/unlike: ").strip()

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        print("❌ Invalid TIMESTAMP.")
        return

    post = posts.get(post_timestamp)
    if not post:
        print("❌ No post found with that TIMESTAMP.")
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
    print(f"✅ {action} sent to {target_user}.")


def handle(msg: dict, addr: tuple):
    action = msg.get("ACTION", "").upper()
    from_user = msg.get("FROM")
    to_user = msg.get("TO")
    post_timestamp = msg.get("POST_TIMESTAMP")

    if action not in ["LIKE", "UNLIKE"] or not from_user or not to_user or not post_timestamp:
        if VERBOSE:
            print("⚠️ Malformed LIKE/UNLIKE message.")
        return

    try:
        post_timestamp = int(post_timestamp)
    except ValueError:
        if VERBOSE:
            print("⚠️ Invalid POST_TIMESTAMP.")
        return

    post = posts.get(post_timestamp)
    if not post:
        if VERBOSE:
            print(f"⚠️ LIKE received for unknown post timestamp: {post_timestamp}")
        return

    if to_user != local_profile["USER_ID"]:
        return  # Not for us

    preview = post.get("CONTENT", post.get("message", ""))[:30]

    if VERBOSE:
        print(f"💬 {action} received from {from_user} on post {post_timestamp}")
    elif action == "LIKE":
        print(f"{from_user.split('@')[0]} likes your post [{preview}]")
    elif action == "UNLIKE":
        print(f"{from_user.split('@')[0]} unliked your post [{preview}]")
