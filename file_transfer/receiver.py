import base64
import os
import time
from state import file_transfers, local_profile, get_peer_address
from utils import validate_token
from message import build_message
from socket_handler import send_unicast
from config import settings
from file_transfer.sender import start_sending_chunks
from file_transfer.file_session import get_session, remove_session
from handlers import ack


RECEIVED_DIR = "downloads"
os.makedirs(RECEIVED_DIR, exist_ok=True)

# Offer reception and manual acceptance logic
def handle_file_offer(message: dict):
    file_id = message.get("FILEID")
    sender = message.get("FROM")
    filename = message.get("FILENAME")
    filesize = message.get("FILESIZE")
    description = message.get("DESCRIPTION", "")
    offer_timestamp = message.get("TIMESTAMP")
    token = message.get("TOKEN")
    sender_ip = get_peer_address(sender)

    if not sender_ip:
        print("❌ Cannot respond, sender IP unknown.")
        return

    if settings["VERBOSE"]:
        print(f"\n📦 Incoming File Offer from {sender}")
        print(f"Filename: {filename}")
        print(f"Size: {filesize} bytes")
        print(f"Description: {description}")
    else:
        print(f"User {sender} is sending you a file. (Enter to proceed)")

    # Prompt to accept or ignore
    choice = input("Do you want to accept the file? (y to accept / anything else to ignore): ").strip().lower()
    now = int(time.time())

    if choice == "y":
        print("✅ File accepted. Preparing to receive chunks...")
        file_transfers[file_id] = {
            "chunks": {},
            "expected": None,
            "filename": filename,
            "timestamp": offer_timestamp,
        }

        response = {
            "TYPE": "FILE_ACCEPT",
            "FROM": local_profile["USER_ID"],
            "TO": sender,
            "FILEID": file_id,
            "TIMESTAMP": now,
        }

    else:
        print("⏳ File ignored.")
        response = {
            "TYPE": "FILE_IGNORED",
            "FROM": local_profile["USER_ID"],
            "TO": sender,
            "FILEID": file_id,
            "TIMESTAMP": now,
            "REASON": "User ignored file offer"
        }

    send_unicast(build_message(response), sender_ip)
    if message.get("FILEID"):
        ack.send_ack(sender, message["FILEID"])



def handle_file_chunk(message: dict):
    file_id = message.get("FILEID")
    sender = message.get("FROM")
    token = message.get("TOKEN")

    try:
        chunk_index = int(message.get("CHUNK_INDEX"))
        total_chunks = int(message.get("TOTAL_CHUNKS"))
        chunk_size = int(message.get("CHUNK_SIZE", 0))
        data = message.get("DATA")
    except (ValueError, TypeError):
        print("❌ Invalid chunk index or total.")
        return

    if not all([file_id, data, token]):
        print("❌ Malformed FILE_CHUNK message.")
        return

    if not validate_token(token, expected_scope="file"):
        print("❌ Invalid or expired token in FILE_CHUNK.")
        return

    if file_id not in file_transfers:
        print(f"⚠️ Unknown FILEID: {file_id}. Ignoring.")
        return

    transfer = file_transfers[file_id]
    chunks = transfer.setdefault("chunks", {})

    try:
        binary_data = base64.b64decode(data)
        chunks[chunk_index] = binary_data
    except Exception as e:
        print(f"❌ Error decoding chunk: {e}")
        return

    if transfer.get("expected") is None:
        transfer["expected"] = total_chunks

    received = len(chunks)
    if settings["VERBOSE"]:
        print(f"[VERBOSE] Received chunk {chunk_index + 1}/{total_chunks} for {transfer.get('filename')}")

    if received == total_chunks and all(i in chunks for i in range(total_chunks)):
        chunks_ordered = [chunks[i] for i in range(total_chunks)]
        filepath = os.path.join(os.getcwd(), "downloads", transfer["filename"])

        with open(filepath, "wb") as f:
            for chunk in chunks_ordered:
                f.write(chunk)

        print(f"✅ File received and saved to: {filepath}")
        send_file_received(sender, file_id)
        if message.get("FILEID"):
            ack.send_ack(sender, message["FILEID"])


def handle_file_received(message: dict, verbose=False):
    # do nothing unless in verbose mode
    if not settings["VERBOSE"]:
        return

    file_id = message.get("FILEID")
    sender = message.get("FROM")
    status = message.get("STATUS")

    if file_id and sender and status:
        print(f"[VERBOSE] ✅ {sender} reported {status} for file ID {file_id}")

def send_file_received(to_user_id: str, file_id: str):
    ack = {
        "TYPE": "FILE_RECEIVED",
        "FROM": local_profile["USER_ID"],
        "TO": to_user_id,
        "FILEID": file_id,
        "STATUS": "COMPLETE",
        "TIMESTAMP": int(time.time())
    }

    sender_ip = get_peer_address(to_user_id)
    session = get_session(file_id)
    if sender_ip:
        if session:
            remove_session(file_id)
        send_unicast(build_message(ack), sender_ip)

def handle_file_accept(message: dict):
    file_id = message.get("FILEID")
    to_user = message.get("FROM")
    session = get_session(file_id)
    print(f"[VERBOSE] ✅ File offer accepted by {to_user} (FILEID: {file_id})")

    # Reconstruct original file path based on FILEID
    if file_id in file_transfers:
        original_filename = file_transfers[file_id]["filename"]
        original_path = os.path.join(os.getcwd(), "downloads", original_filename)
        start_sending_chunks(file_id, to_user, original_path)
    if not session:
        print("⚠️ No matching file transfer session found.")
