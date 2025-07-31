from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp
from state import tokens, revoked_tokens, peers, local_profile

# ========== Constants ==========
DEFAULT_SCOPE = "POST,DM,FILE"
DEFAULT_EXPIRY = 3600  # 1 hour in seconds

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    if msg_type == "TOKEN_REQUEST":
        handle_request(msg, addr)
    elif msg_type == "TOKEN_REPLY":
        handle_reply(msg, addr)
    elif msg_type == "TOKEN_REVOKE":
        handle_revoke(msg, addr)

def handle_request(msg: dict, addr: tuple):
    requester = msg.get("USER")
    if not requester:
        return

    token_id = generate_message_id()
    issue_time = current_unix_timestamp()
    expiry_time = issue_time + DEFAULT_EXPIRY

    token_str = f"TOKEN-{token_id}"
    tokens[token_str] = {
        "USER": requester,
        "ISSUER": local_profile.USER_ID,
        "SCOPE": DEFAULT_SCOPE,
        "ISSUED_AT": issue_time,
        "EXPIRES_AT": expiry_time
    }

    fields = {
        "TYPE": "TOKEN_REPLY",
        "ID": generate_message_id(),
        "TIME": str(issue_time),
        "USER": local_profile.USER_ID,
        "TO": requester,
        "TOKEN": token_str,
        "SCOPE": DEFAULT_SCOPE,
        "EXPIRY": str(expiry_time)
    }

    if requester in peers:
        peer_ip = peers[requester]["ADDRESS"]
        send_unicast(build_message(fields), peer_ip)
        print(f"🔐 TOKEN_REPLY sent to {requester}")

def handle_reply(msg: dict, addr: tuple):
    token = msg.get("TOKEN")
    scope = msg.get("SCOPE", DEFAULT_SCOPE)
    expiry = int(msg.get("EXPIRY", current_unix_timestamp() + DEFAULT_EXPIRY))
    issuer = msg.get("USER")
    user = msg.get("TO")

    if user != local_profile.USER_ID or not token:
        return

    tokens[token] = {
        "USER": local_profile.USER_ID,
        "ISSUER": issuer,
        "SCOPE": scope,
        "ISSUED_AT": current_unix_timestamp(),
        "EXPIRES_AT": expiry
    }

    print(f"✅ TOKEN_RECEIVED from {issuer} (expires in {expiry - current_unix_timestamp()}s)")

def handle_revoke(msg: dict, addr: tuple):
    token = msg.get("TOKEN")
    reason = msg.get("REASON", "No reason provided")
    revoked_tokens[token] = reason
    if token in tokens:
        del tokens[token]
    print(f"❌ TOKEN revoked: {token} ({reason})")

# ========== CLI ==========
def cli_request():
    to_user = input("USER ID to request token from: ").strip()
    if to_user not in peers:
        print("❌ Unknown user.")
        return

    msg = build_message({
        "TYPE": "TOKEN_REQUEST",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": local_profile.USER_ID,
        "TO": to_user
    })

    peer_ip = peers[to_user]["ADDRESS"]
    send_unicast(msg, peer_ip)
    print(f"🔐 TOKEN_REQUEST sent to {to_user}")

def cli_revoke():
    token = input("Token string to revoke: ").strip()
    reason = input("Reason for revocation: ").strip()

    msg = build_message({
        "TYPE": "TOKEN_REVOKE",
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": local_profile.USER_ID,
        "TOKEN": token,
        "REASON": reason or "Revoked by user"
    })

    if token not in tokens:
        print("⚠️  Token not in local store, will broadcast anyway.")

    # Optionally broadcast to all known peers
    for uid, peer in peers.items():
        send_unicast(msg, peer["ADDRESS"])

    print(f"❌ TOKEN_REVOKE broadcasted.")

# ========== Validation ==========
def validate(token: str, required_scope: str) -> bool:
    if token in revoked_tokens:
        return False
    if token not in tokens:
        return False
    info = tokens[token]
    if current_unix_timestamp() > info["EXPIRES_AT"]:
        return False
    return required_scope.upper() in info["SCOPE"].upper().split(",")
