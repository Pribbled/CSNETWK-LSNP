from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp, generate_token
from state import peers, tokens, revoked_tokens, dm_history, local_profile, get_peer_address
from config import settings

# ========== Color Constants ==========
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "DM":
        return

    required = ["TYPE", "FROM", "TO", "CONTENT", "TIMESTAMP", "MESSAGE_ID", "TOKEN"]
    if not all(k in msg for k in required):
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️  Malformed DM{RESET}")
        return

    recipient = msg["TO"]
    # print(recipient)
    # print(local_profile['USER_ID'])
    if recipient.lower() != local_profile["USER_ID"].lower():
        if settings["VERBOSE"]:
            print(f"{YELLOW}📩 DM not for this user ({recipient} != {local_profile['USER_ID']}){RESET}")
        return

    token = msg["TOKEN"]
    if not token or token in revoked_tokens:
        if settings["VERBOSE"]:
            print(f"{RED}❌ Rejected DM: invalid or revoked token.{RESET}")
        return

    if token in tokens:
        expiry = tokens[token]["EXPIRES_AT"]
        if current_unix_timestamp() > expiry:
            if settings["VERBOSE"]:
                print(f"{RED}❌ Rejected DM: token expired.{RESET}")
            return

    sender = msg["FROM"]
    content = msg["CONTENT"]
    display_name = peers.get(sender, {}).get("NAME", sender)

    if settings["VERBOSE"]:
        print(f"\n{CYAN}💬 DM received from {sender} to {recipient}: {content}{RESET}")
    else:
        print(f"{CYAN}{display_name}: {content}{RESET}")

    dm_history.append({
        "FROM": sender,
        "TO": recipient,
        "CONTENT": content,
        "TIMESTAMP": msg["TIMESTAMP"]
    })


# ========== CLI ==========
def cli_send():
    if not peers:
        print(f"{RED}❌ No known peers. Receive a PROFILE first.{RESET}")
        return

    print(f"{CYAN}Known peers:{RESET}")
    for uid, info in peers.items():
        ip = get_peer_address(uid)
        name = info.get('NAME', '')
        print(f" - {uid} @ {ip} (name: {name})")

        if not ip:
            print(f"{RED}❌ Could not resolve IP for {uid}{RESET}")
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
        print(f"{RED}❌ Unknown recipient.{RESET}")
        return

    peer_info = peers[matched_uid]
    ip = peer_info.get("ADDRESS")
    if not ip:
        print(f"{RED}❌ Could not determine recipient IP.{RESET}")
        return

    content = input("Message content: ").strip()
    if not content:
        print(f"{RED}❌ Cannot send empty message.{RESET}")
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

    if settings["VERBOSE"]:
        print(f"{CYAN}📤 Sending DM to {matched_uid} at {ip}...\nMessage:\n{msg}{RESET}")

    send_unicast(msg, ip)
    print(f"{GREEN}✅ DM sent.{RESET}")
