from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp, generate_token
from state import peers, tokens, revoked_tokens, dm_history, local_profile, get_peer_address
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
    if recipient.lower() != local_profile["USER_ID"].lower():
        if config.VERBOSE:
            print(f"📩 DM not for this user ({recipient} != {local_profile['USER_ID']})")
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
        print(f"\n💬 DM received from {sender} to {recipient}: {content}")
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
        ip = get_peer_address(uid)
        name = info.get('NAME', '')
        print(f" - {uid} ({ip}) (name: {name})")

        if not ip:
            print(f"❌ Could not resolve IP for {uid}")
            return

    # Ask for username input
    input_uid = input("Recipient USER ID: ").strip()
    if "@" in input_uid:
        input_username = input_uid.split("@")[0].lower()
    else:
        input_username = input_uid.lower()

    # Match by username
    matched_uid = None
    for uid in peers:
        peer_username = uid.split("@")[0].lower()
        if peer_username == input_username:
            matched_uid = uid
            break

    if not matched_uid:
        print("❌ Unknown recipient.")
        return

    peer_info = peers[matched_uid]
    ip = peer_info.get("ADDRESS")
    if not ip:
        print("❌ Could not determine recipient IP.")
        return

    content = input("Message content: ").strip()
    if not content:
        print("❌ Cannot send empty message.")
        return

    from_user = local_profile["USER_ID"]
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(from_user, timestamp, ttl, "chat")

    fields = {
        "TYPE": "DM",
        "FROM": from_user,
        "TO": matched_uid,
        "CONTENT": content,
        "TIMESTAMP": str(timestamp),
        "MESSAGE_ID": generate_message_id(),
        "TOKEN": token
    }

    msg = build_message(fields)

    if config.VERBOSE:
        print(f"📤 Sending DM to {matched_uid} at {ip}...\nMessage:\n{msg}")

    send_unicast(msg, ip)
    print("✅ DM sent.")
