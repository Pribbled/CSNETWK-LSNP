from message import build_message
from socket_handler import send_unicast
from utils import (
    generate_message_id,
    current_unix_timestamp,
    validate_token,
    RED, GREEN, YELLOW, CYAN, BLUE, RESET
)
from state import local_profile, peers, follow_map, revoked_tokens
from config import settings

# ========== RECEIVE ==========
# ========== RECEIVE ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    from_id = msg.get("FROM")
    to_id = msg.get("TO")
    token = msg.get("TOKEN")
    timestamp = msg.get("TIMESTAMP")
    message_id = msg.get("MESSAGE_ID")

    if to_id != local_profile["USER_ID"] or not from_id or not token or not timestamp:
        return

    if not validate(token, "FOLLOW"):
        print(f"{YELLOW}⚠️ Invalid or expired token from {from_id}. Ignoring {msg_type}.{RESET}")
        return
    
    if token in revoked_tokens:
        print("❌ Cannot send, token has been revoked.")
        return


    if msg_type == "FOLLOW":
        if from_id not in follow_map:
            follow_map[from_id] = {}

        if settings["VERBOSE"]:
            print(f"""{CYAN}[{timestamp}] < {addr[0]}:{addr[1]}
{BLUE}TYPE:{RESET} FOLLOW
{BLUE}MESSAGE_ID:{RESET} {message_id}
{BLUE}FROM:{RESET} {from_id}
{BLUE}TO:{RESET} {to_id}
{BLUE}TIMESTAMP:{RESET} {timestamp}
{BLUE}TOKEN: {token}{RESET}\n""")
            print(f"User {from_id.split('@')[0]} has followed you")
        else:
            print(f"User {from_id.split('@')[0]} has followed you")

    elif msg_type == "UNFOLLOW":
        if from_id in follow_map:
            del follow_map[from_id]

        if settings["VERBOSE"]:
            print(f"""{CYAN}[{timestamp}] < {addr[0]}:{addr[1]}
{BLUE}TYPE:{RESET} UNFOLLOW
{BLUE}MESSAGE_ID:{RESET} {message_id}
{BLUE}FROM:{RESET} {from_id}
{BLUE}TO:{RESET} {to_id}
{BLUE}TIMESTAMP:{RESET} {timestamp}
{BLUE}TOKEN: {token}{RESET}\n""")
            print(f"User {from_id.split('@')[0]} has unfollowed you")
        else:
            print(f"User {from_id.split('@')[0]} has unfollowed you")

# ========== CLI ==========
def cli_follow():
    target = input("Enter USER_ID to follow: ").strip()
    if target not in peers:
        print(f"{RED}❌ User not known.{RESET}")
        return

    token = input("Enter your valid FOLLOW-scope token: ").strip()
    if not validate_token(token, "FOLLOW"):
        print(f"{RED}❌ Invalid or expired token.{RESET}")
        return

    msg = build_message({
        "TYPE": "FOLLOW",
        "MESSAGE_ID": generate_message_id(),
        "FROM": local_profile["USER_ID"],
        "TO": target,
        "TIMESTAMP": str(current_unix_timestamp()),
        "TOKEN": token
    })

    send_unicast(msg, peers[target]["ADDRESS"])
    print(f"{GREEN}✅ Follow request sent to {target}{RESET}")

def cli_unfollow():
    target = input("Enter USER_ID to unfollow: ").strip()
    if target not in peers:
        print(f"{RED}❌ User not known.{RESET}")
        return

    token = input("Enter your valid FOLLOW-scope token: ").strip()
    if not validate_token(token, "FOLLOW"):
        print(f"{RED}❌ Invalid or expired token.{RESET}")
        return

    msg = build_message({
        "TYPE": "UNFOLLOW",
        "MESSAGE_ID": generate_message_id(),
        "FROM": local_profile["USER_ID"],
        "TO": target,
        "TIMESTAMP": str(current_unix_timestamp()),
        "TOKEN": token
    })

    send_unicast(msg, peers[target]["ADDRESS"])
    print(f"{GREEN}✅ Unfollow request sent to {target}{RESET}")
