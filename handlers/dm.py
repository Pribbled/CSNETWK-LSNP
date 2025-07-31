from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp, generate_token
from state import peers, tokens, revoked_tokens, dm_history, local_profile
import config


# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "DM":
        return

    required = ["TYPE", "FROM", "TO", "CONTENT", "TIMESTAMP", "MESSAGE_ID", "TOKEN"]
    if not all(k in msg for k in required):
        if config.VERBOSE:
            print("⚠️  Malformed DM")
        return

    recipient = msg["TO"]
    if recipient != local_profile["USER_ID"]:
        if config.VERBOSE:
            print(f"📩 DM not intended for this user ({recipient} != {local_profile['USER_ID']})")
        return

    token = msg["TOKEN"]
    if not token or token in revoked_tokens:
        if config.VERBOSE:
            print("❌ Rejected DM: invalid or revoked token.")
        return

    if token in tokens:
        expiry = tokens[token]["EXPIRES_AT"]
        if current_unix_timestamp() > expiry:
            if config.VERBOSE:
                print("❌ Rejected DM: token expired.")
            return

    sender = msg["FROM"]
    content = msg["CONTENT"]

    display_name = peers.get(sender, {}).get("NAME", sender)

    if config.VERBOSE:
        print(f"\n💬 DM from {sender} to {recipient}: {content}")
    else:
        print(f"{display_name}: {content}")

    dm_history.append({
        "FROM": sender,
        "TO": recipient,
        "CONTENT": content,
        "TIMESTAMP": msg["TIMESTAMP"]
    })


# ========== CLI ==========
def cli_send():
    if not peers:
        print("❌ No known peers. Receive a PROFILE first.")
        return

    print("Known peers:")
    for uid, info in peers.items():
        print(f" - {uid}: {info.get('NAME', '')} @ {info.get('ADDRESS')}")

    to_user = input("Recipient USER ID: ").strip()
    content = input("Message content: ").strip()

    if to_user not in peers:
        print("❌ Unknown recipient.")
        return

    from_user = local_profile["USER_ID"]
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(from_user, timestamp, ttl, "chat")

    fields = {
        "TYPE": "DM",
        "FROM": from_user,
        "TO": to_user,
        "CONTENT": content,
        "TIMESTAMP": str(timestamp),
        "MESSAGE_ID": generate_message_id(),
        "TOKEN": token
    }

    msg = build_message(fields)
    ip = peers[to_user]["ADDRESS"]
    send_unicast(msg, ip)
    print("✅ DM sent.")
