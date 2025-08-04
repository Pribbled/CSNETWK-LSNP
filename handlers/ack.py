# ack.py

from message import build_message
from socket_handler import send_unicast
from state import peers, local_profile, verbose
from utils import log_verbose

# Track ACKs we've already sent (to avoid sending duplicates)
_sent_acks = set()

def send_ack(to_user_id, original_message_id):
    if original_message_id in _sent_acks:
        return  # Skip duplicate ACK

    addr = peers.get(to_user_id, {}).get("ADDRESS")
    if not addr:
        if verbose:
            log_verbose("ACK", f"Could not find address for user {to_user_id}")
        return

    ack_payload = {
        "TYPE": "ACK",
        "MESSAGE_ID": original_message_id,
        "STATUS": "RECEIVED"
    }

    message = build_message(ack_payload)
    send_unicast(message, addr)
    _sent_acks.add(original_message_id)

    if verbose:
        log_verbose("ACK", f"Sent ACK for message {original_message_id} to {to_user_id}")
