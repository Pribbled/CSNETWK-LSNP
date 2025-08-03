import os
import base64
import uuid
import time
from utils import generate_token
from state import local_profile, get_peer_address
from message import build_message
from socket_handler import send_unicast

CHUNK_SIZE = 4096 

def send_file_offer(to_user_id, file_path, description=""):
    if not os.path.isfile(file_path):
        print("❌ File does not exist.")
        return

    filename = os.path.basename(file_path)
    filesize = os.path.getsize(file_path)
    filetype = "application/octet-stream"  # Default MIME type
    file_id = uuid.uuid4().hex

    timestamp = int(time.time())
    ttl = 3600
    token = generate_token(user_id=local_profile["USER_ID"], ttl=ttl, scope="file", timestamp=timestamp)

    offer_msg = {
        "TYPE": "FILE_OFFER",
        "FROM": local_profile["USER_ID"],
        "TO": to_user_id,
        "FILENAME": filename,
        "FILESIZE": filesize,
        "FILETYPE": filetype,
        "FILEID": file_id,
        "DESCRIPTION": description,
        "TIMESTAMP": timestamp,
        "TOKEN": token
    }

    peer_ip = get_peer_address(to_user_id)
    if not peer_ip:
        print(f"❌ Could not find IP for {to_user_id}")
        return

    send_unicast(build_message(offer_msg), peer_ip)
    return file_id  # Needed for follow-up chunk sending


def send_file_chunks(to_user_id, file_path, file_id):
    chunk_size = 1024  # Max per RFC is sender-defined
    timestamp = int(time.time())
    ttl = 3600  # or any value you want
    print("sending files from ", local_profile["USER_ID"], " to ", to_user_id)
    token = generate_token(user_id=local_profile["USER_ID"], ttl=3600, scope="file", timestamp=timestamp)
    with open(file_path, "rb") as f:
        data = f.read()

    total_chunks = (len(data) + chunk_size - 1) // chunk_size

    for idx in range(total_chunks):
        chunk = data[idx * chunk_size:(idx + 1) * chunk_size]
        encoded = base64.b64encode(chunk).decode()

        chunk_msg = {
            "TYPE": "FILE_CHUNK",
            "FROM": local_profile["USER_ID"],
            "TO": to_user_id,
            "FILEID": file_id,
            "CHUNK_INDEX": idx,
            "TOTAL_CHUNKS": total_chunks,
            "CHUNK_SIZE": len(chunk),
            "TOKEN": token,
            "DATA": encoded
        }

        peer_ip = get_peer_address(to_user_id)
        if not peer_ip:
            print(f"❌ Could not find IP for {to_user_id}")
            return

        send_unicast(build_message(chunk_msg), peer_ip)

def start_sending_chunks(file_id: str, to_user_id: str, filepath: str):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    try:
        filesize = os.path.getsize(filepath)
        total_chunks = (filesize + CHUNK_SIZE - 1) // CHUNK_SIZE
        token = generate_token(
            user_id=local_profile["USER_ID"],
            timestamp=int(time.time()),
            ttl=3600,
            scope="file"
        )

        peer_ip = get_peer_address(to_user_id)

        if not peer_ip:
            print(f"❌ Cannot send chunks, IP unknown for {to_user_id}")
            return

        with open(filepath, "rb") as f:
            for index in range(total_chunks):
                chunk_data = f.read(CHUNK_SIZE)
                encoded_data = base64.b64encode(chunk_data).decode("utf-8")

                chunk_message = {
                    "TYPE": "FILE_CHUNK",
                    "FROM": local_profile["USER_ID"],
                    "TO": to_user_id,
                    "FILEID": file_id,
                    "CHUNK_INDEX": str(index),
                    "TOTAL_CHUNKS": str(total_chunks),
                    "CHUNK_SIZE": str(len(chunk_data)),
                    "DATA": encoded_data,
                    "TOKEN": token
                }

                send_unicast(build_message(chunk_message), peer_ip)
                time.sleep(0.05)  # slight delay to prevent flooding

        print(f"✅ All chunks sent to {to_user_id} for FILEID {file_id}")

    except Exception as e:
        print(f"❌ Error while sending chunks: {e}")

def handle_file_accept(message: dict):
    file_id = message.get("FILEID")
    to_user = message.get("FROM")
    print(f"✅ File offer accepted by {to_user} (FILEID: {file_id})")
    # Start sending chunks now...
    start_sending_chunks(file_id, to_user)
