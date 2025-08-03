import os
import base64
import uuid
import time
from utils import generate_token
from state import local_profile, get_peer_address
from message import build_message
from socket_handler import send_unicast

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
