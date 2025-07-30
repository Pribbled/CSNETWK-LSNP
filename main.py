# main.py

from udp_socket import UDPSocket
from message_parsing import parseMessage, buildMessage
from file_transfer import handleFileOffer, sendFileOffer, sendFileChunks
from token_mng import generateToken
from TicTacToe import playGame
from IPLog import addressLog

import threading
import time
import socket

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

display_name = input("Enter your display name: ").strip()
user_id = f"{display_name}@{get_local_ip()}"
print(f"[INIT] Your USER_ID: {user_id}")


known_peers = {}  # {user_id: ip}
udp = UDPSocket(verbose=True)


def handle_message(msg, addr):
    parsed = parseMessage(msg)
    msg_type = parsed.get("TYPE", "")
    sender = parsed.get("USER_ID") or parsed.get("FROM")
    ip = addr[0]

    if msg_type == "PROFILE":
        known_peers[sender] = ip
        print(f"[DISCOVER] {sender} is online.")

    elif msg_type == "POST":
        print(f"[POST] {sender}: {parsed.get('CONTENT')}")

    elif msg_type == "DM":
        print(f"[DM] {parsed.get('FROM')} → You: {parsed.get('CONTENT')}")

    elif msg_type == "FILE_OFFER":
        handleFileOffer(parsed)

    elif msg_type == "TICTACTOE_MOVE":
        print("[TICTACTOE] Move received (handled by TicTacToe module).")

    elif msg_type == "ACK":
        print("[ACK] Received ACK.")

    else:
        print(f"[INFO] Unrecognized TYPE: {msg_type}")

# Start listening
udp.receive(handle_message)

def menu():
    print("\n=== LSNP Menu ===")
    print("1. Send PROFILE")
    print("2. Send POST")
    print("3. Send DM")
    print("4. Send FILE")
    print("5. Play TicTacToe")
    print("6. Show known peers")
    print("7. Start IP Log")
    print("0. Exit")

while True:
    menu()
    choice = input("Choose an option: ")

    if choice == "1":
        profile = buildMessage({
            "TYPE": "PROFILE",
            "USER_ID": user_id,
            "DISPLAY_NAME": display_name,
            "STATUS": "Online"
        })
        udp.sendToAll(profile)

    elif choice == "2":
        content = input("Enter your post: ")
        post = buildMessage({
            "TYPE": "POST",
            "USER_ID": user_id,
            "CONTENT": content
        })
        udp.sendToAll(post)

    elif choice == "3":
        to_user = input("Recipient user_id: ")
        if to_user not in known_peers:
            print("User not known. Send PROFILE first.")
            continue
        content = input("Message: ")
        dm = buildMessage({
            "TYPE": "DM",
            "FROM": user_id,
            "TO": to_user,
            "CONTENT": content
        })
        udp.sendToOne(dm, known_peers[to_user])

    elif choice == "4":
        to_user = input("Recipient user_id: ")
        if to_user not in known_peers:
            print("User not known.")
            continue
        file_path = input("Path to file: ")
        file_id = sendFileOffer(user_id, to_user, file_path, known_peers[to_user])
        time.sleep(1)
        sendFileChunks(user_id, to_user, file_path, file_id, udp)

    elif choice == "5":
        peer_uid = input("Opponent user_id: ")
        if peer_uid not in known_peers:
            print("User not found.")
            continue
        symbol = input("Choose symbol (X or O): ").upper()
        is_first = (symbol == "X")
        peer_ip = known_peers[peer_uid]
        threading.Thread(target=playGame, args=(user_id, peer_ip, symbol, is_first), daemon=True).start()

    elif choice == "6":
        print("Known peers:")
        for uid, ip in known_peers.items():
            print(f"- {uid} at {ip}")

    elif choice == "7":
        threading.Thread(target=addressLog, daemon=True).start()
        print("IP Logging started in background...")

    elif choice == "0":
        print("Exiting LSNP.")
        break

    else:
        print("Invalid option.")

    time.sleep(0.3)
