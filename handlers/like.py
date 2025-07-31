import config
from state import local_profile, posts

def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "LIKE":
        return

    from_user = msg.get("FROM", "")
    to_user = msg.get("TO", "")
    post_ts = msg.get("POST_TIMESTAMP", "")
    action = msg.get("ACTION", "").upper()
    timestamp = msg.get("TIMESTAMP", "")
    token = msg.get("TOKEN", "")

    if to_user != local_profile.get("USER_ID"):
        return  # Not for us

    try:
        post_ts = int(post_ts)
    except ValueError:
        if config.VERBOSE:
            print(f"⚠️ Invalid post timestamp: {post_ts}")
        return

    post_data = posts.get(post_ts)
    if not post_data:
        if config.VERBOSE:
            print(f"⚠️  LIKE received for unknown post timestamp: {post_ts}")
        return

    if config.VERBOSE:
        print(f"💬 {action} received from {from_user} on post {post_ts}")
    elif action == "LIKE":
        print(f"{from_user.split('@')[0]} likes your post [{post_data['message']}]")
    elif action == "UNLIKE":
        print(f"{from_user.split('@')[0]} unliked your post [{post_data['message']}]")
