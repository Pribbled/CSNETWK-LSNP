import os
import base64
from pathlib import Path
from message import build_message
from socket_handler import send_unicast
from utils import generate_message_id, current_unix_timestamp
from state import file_transfers, peers
import config

CHUNK_SIZE = 1024  # 1KB

# ========== Receive ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    if msg_type == "FILE_OFFER":
        handle_offer(msg, addr)
    elif msg_type == "FILE_ACCEPT":
        handle_accept(msg, addr)
    elif msg_type == "FILE_REJECT":
        handle_reject(msg, addr)
    elif msg_type == "FILE_CHUNK":
        handle_chunk(msg, addr)

def handle_offer(msg: dict, addr: tuple):
    file_id = msg.get("ID")
    user = msg.get("USER")
    filename = msg.get("FILENAME")
    size = msg.get("SIZE")

    if not all([file_id, user, filename, size]):
        print("⚠️  Malformed FILE_OFFER")
        return

    print(f"\n📁 {user} is offering file '{filename}' ({size} bytes)")
    choice = input("Accept file? (y/n): ").strip().lower()

    reply_type = "FILE_ACCEPT" if choice == "y" else "FILE_REJECT"

    reply = build_message({
        "TYPE": reply_type,
        "ID": generate_message_id(),
        "TIME": str(current_unix_timestamp()),
        "USER": config.USER_ID,
        "TO": user,
        "FILE_ID": file_id
    })

    peer_ip = addr[0]
    send_unicast(reply, peer_ip)

    if reply_type == "FILE_ACCEPT":
        file_transfers[file_id] = {
            "FILENAME": filename,
            "FROM": user,
            "CHUNKS": {},
            "TOTAL": None
        }

def handle_accept(msg: dict, addr: tuple):
    file_id = msg.get("FILE_ID")
    to_user = msg.get("TO")
    from_user = msg.get("USER")

    if to_user != config.USER_ID or file_id not in file_transfers:
        return

    info = file_transfers[file_id]
    filename = info["FILENAME"]
    peer_ip = addr[0]
    filepath = Path("shared") / filename

    if not filepath.exists():
        print("❌ File missing.")
        return

    size = filepath.stat().st_size
    total_chunks = (size + CHUNK_SIZE - 1) // CHUNK_SIZE
    file_transfers[file_id]["TOTAL"] = total_chunks

    with open(filepath, "rb") as f:
        for i in range(total_chunks):
            chunk = f.read(CHUNK_SIZE)
            b64 = base64.b64encode(chunk).decode("utf-8")
            chunk_msg = build_message({
                "TYPE": "FILE_CHUNK",
                "ID": generate_message_id(),
                "TIME": str(current_unix_timestamp()),
                "USER": config.USER_ID,
                "TO": from_user,
                "FILE_ID": file_id,
                "INDEX": str(i),
                "DATA": b64
            })
            send_unicast(chunk_msg, peer_ip)

    print(f"📤 File '{filename}' sent in {total_chunks} chunks.")

def handle_reject(msg: dict, addr: tuple):
    file_id = msg.get("FILE_ID")
    user = msg.get("USER")
    print(f"❌ {user} rejected file transfer {file_id}")

def handle_chunk(msg: dict, addr: tuple):
    file_id = msg.get("FILE_ID")
    index = int(msg.get("INDEX", -1))
    data = msg.get("DATA")

    if file_id not in file_transfers:
        return

    if index == -1 or not data:
        print("⚠️  Invalid FILE_CHUNK")
        return

    chunk_data = base64.b64decode(data.encode("utf-8"))
    file_transfers[file_id]["CHUNKS"][index] = chunk_data

    chunks = file_transfers[file_id]["CHUNKS"]
    total = file_transfers[file_id].get("TOTAL")

    if total is not None and len(chunks) == total:
        filename = file_transfers[file_id]["FILENAME"]
        save_path = Path("downloads") / filename
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            for i in range(total):
                f.write(chunks[i])

        print(f"✅ File '{filename}' saved to 'downloads/'")

# ========== CLI ==========
def cli_send():
    to_user = input("Recipient USER ID: ").strip()
    filepath = input("Path to file: ").strip()

    if not os.path.exists(filepath):
        print("❌ File not found.")
        return

    filename = os.path.basename(filepath)
    size = os.path.getsize(filepath)
    file_id = generate_message_id()

    file_transfers[file_id] = {
        "FILENAME": filename,
        "FROM": config.USER_ID,
        "FILEPATH": filepath
    }

    fields = {
        "TYPE": "FILE_OFFER",
        "ID": file_id,
        "TIME": str(current_unix_timestamp()),
        "USER": config.USER_ID,
        "TO": to_user,
        "FILENAME": filename,
        "SIZE": str(size)
    }

    if to_user not in peers:
        print("❌ Unknown peer.")
        return

    peer_ip = peers[to_user]["ADDRESS"]
    msg = build_message(fields)
    send_unicast(msg, peer_ip)

    print(f"📁 FILE_OFFER sent to {to_user}")
