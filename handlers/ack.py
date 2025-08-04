# ack.py
from utils import YELLOW, GREEN, RESET
from message import build_message
from socket_handler import send_unicast
from state import peers
from config import settings

# Track ACKs we've already sent (to avoid duplicates)
_sent_acks = set()

def send_ack(to_user_id, original_message_id):
    if original_message_id in _sent_acks:
        return  # Skip duplicate ACK

    addr = peers.get(to_user_id, {}).get("ADDRESS")
    if not addr:
        if settings["VERBOSE"]:
            print(f"⚠️: Could not find address for user {to_user_id}")
        return

    ack_payload = {
        "TYPE": "ACK",
        "MESSAGE_ID": original_message_id,
        "STATUS": "RECEIVED"
    }

    message = build_message(ack_payload)
    send_unicast(message, addr)
    _sent_acks.add(original_message_id)

    if settings["VERBOSE"]:
        print(f"📨: Sent ACK for message {original_message_id} to {to_user_id}")

# ===== Handle received ACKs =====
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE") != "ACK":
        return

    required = ["TYPE", "MESSAGE_ID", "STATUS"]
    if not all(k in msg for k in required):
        if settings["VERBOSE"]:
            print(f"{YELLOW}⚠️ Malformed ACK received: {msg}{RESET}")
        return

    message_id = msg["MESSAGE_ID"]
    status = msg["STATUS"]
    from_ip = addr[0]

    # Try to resolve the sender's user ID
    sender_id = None
    for uid, info in peers.items():
        if info.get("ADDRESS") == from_ip:
            sender_id = uid
            break

    if settings["VERBOSE"]:
        print(f"📫: Received ACK from {sender_id or from_ip} for message {message_id}, status: {status}")
    else:
        # print(f"{GREEN}✅ Message {message_id} was acknowledged by {sender_id or from_ip}.{RESET}")
        pass