from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp
from state import config, peers, follow_map
from handlers.token import validate

# ========== RECEIVE ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    from_id = msg.get("FROM")
    to_id = msg.get("TO")
    token = msg.get("TOKEN")

    # Only accept messages for self
    if to_id != config.USER_ID or not from_id or not token:
        return

    if not validate(token, "FOLLOW"):
        print(f"⚠️ Invalid or expired token from {from_id}. Ignoring {msg_type}.")
        return

    if msg_type == "FOLLOW":
        if from_id not in follow_map:
            follow_map[from_id] = {}
        print(f"👤 User {from_id} has followed you.")
    elif msg_type == "UNFOLLOW":
        if from_id in follow_map:
            del follow_map[from_id]
        print(f"👤 User {from_id} has unfollowed you.")

# ========== CLI ==========
def cli_follow():
    target = input("Enter USER_ID to follow: ").strip()
    if target not in peers:
        print("❌ User not known.")
        return

    token = input("Enter your valid FOLLOW-scope token: ").strip()
    if not validate(token, "FOLLOW"):
        print("❌ Invalid or expired token.")
        return

    msg = build_message({
        "TYPE": "FOLLOW",
        "FROM": config.USER_ID,
        "TO": target,
        "TIMESTAMP": str(current_unix_timestamp()),
        "MESSAGE_ID": generate_message_id(),
        "TOKEN": token
    })

    send_unicast(msg, peers[target]["ADDRESS"])
    print(f"✅ Follow request sent to {target}")

def cli_unfollow():
    target = input("Enter USER_ID to unfollow: ").strip()
    if target not in peers:
        print("❌ User not known.")
        return

    token = input("Enter your valid FOLLOW-scope token: ").strip()
    if not validate(token, "FOLLOW"):
        print("❌ Invalid or expired token.")
        return

    msg = build_message({
        "TYPE": "UNFOLLOW",
        "FROM": config.USER_ID,
        "TO": target,
        "TIMESTAMP": str(current_unix_timestamp()),
        "MESSAGE_ID": generate_message_id(),
        "TOKEN": token
    })

    send_unicast(msg, peers[target]["ADDRESS"])
    print(f"✅ Unfollow request sent to {target}")
