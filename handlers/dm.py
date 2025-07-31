from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp
from state import peers, tokens, revoked_tokens, dm_history
import config

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "DM":
        return

    required = ["ID", "TIME", "USER", "TO", "CONTENT", "TOKEN"]
    if not all(k in msg for k in required):
        if config.VERBOSE:
            print("⚠️  Malformed DM")
        return

    recipient = msg["TO"]
    if recipient != config.USER_ID:
        if config.VERBOSE:
            print(f"📩 DM not intended for this user ({recipient} != {config.USER_ID})")
        return

    # Validate token
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

    sender = msg["USER"]
    content = msg["CONTENT"]

    print(f"\n💬 DM from {sender}: {content}")
    dm_history.append({
        "FROM": sender,
        "TO": recipient,
        "CONTENT": content,
        "TIME": msg["TIME"]
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
    from_user = input("Your USER ID: ").strip()
    token = input("Token: ").strip()

    if to_user not in peers:
        print("❌ Unknown recipient.")
        return

    fields = {
        "TYPE": "DM",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": from_user,
        "TO": to_user,
        "CONTENT": content,
        "TOKEN": token
    }

    msg = build_message(fields)
    ip = peers[to_user]["ADDRESS"]
    send_unicast(msg, ip)
    print("✅ DM sent.")
