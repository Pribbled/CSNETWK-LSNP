from udp_socket import UDPSocket
from message_parsing import buildMessage, parseMessage
from token_mng import generateToken, isTokenValid
from file_transfer import sendFileOffer, sendFileChunks, handleFileOffer, handleFileChunk
from TicTacToe import playGame
import socket

import time

verbose_mode = True
known_peers = {}   # {user_id: display_name}
received_posts = []  # store messages
revoked_tokens = set()

def getLocalIP():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def handle_message(raw_msg, addr):
    global verbose_mode, known_peers, received_posts
    msg = parseMessage(raw_msg)
    msg_type = msg.get("TYPE", "")
    token = msg.get("TOKEN", "")
    sender = msg.get("USER_ID") or msg.get("FROM")

    if verbose_mode:
        print(f"\n[DEBUG] Raw: {raw_msg}")
        print(f"[DEBUG] Parsed: {msg}")

    if msg_type == "PROFILE":
        display_name = msg.get("DISPLAY_NAME", sender)
        known_peers[user_id] = display_name
        print(f"New peer: {display_name} ({sender})")

    elif msg_type == "POST":
        if not isTokenValid(token, "POST", revoked_tokens):
            print(f"[WARN] Invalid token in POST from {sender}. Ignored.")
            return
        content = msg.get("CONTENT", "")
        received_posts.append((sender, content))
        print(f"📝 {sender}: {content}")

    elif msg_type == "DM":
        if not isTokenValid(token, "DM", revoked_tokens):
            print(f"[WARN] Invalid token in DM from {msg.get('FROM')}. Ignored.")
            return
        print(f"💬 DM from {msg.get('FROM')} → {msg.get('TO')}: {msg.get('CONTENT')}")
    
    elif msg_type == "FILE_OFFER":
        handleFileOffer(msg)

    elif msg_type == "FILE_CHUNK":
        handleFileChunk(msg)


udp = UDPSocket(verbose=True)
udp.receive(handle_message)

print("LSNP Test CLI")
print("Commands: profile, post, dm, peers, messages, sendfile, tictactoe, verbose, exit")

display_name = input("Enter your display name: ").strip()
local_ip = getLocalIP()
user_id = f"{display_name}@{local_ip}"

while True:
    cmd = input(">>> ").strip().lower()

    if cmd == "profile":
        status = input("Status: ")
        profile = buildMessage({
            "TYPE": "PROFILE",
            "USER_ID": user_id,
            "DISPLAY_NAME": name,
            "STATUS": status
        })
        udp.sendToAll(profile)

    elif cmd == "post":
        content = input("Content: ")
        token = generateToken(user_id, ttl=60, scope="POST")
        post = buildMessage({
            "TYPE": "POST",
            "USER_ID": user_id,
            "CONTENT": content,
            "TOKEN": token
        })
        udp.sendToAll(post)
    
    elif cmd == "dm":
        to_id = input("TO (user@ip): ")
        content = input("Content: ")
        token = generateToken(user_id, ttl=60, scope="DM")
        message = buildMessage({
            "TYPE": "DM",
            "FROM": from_id,
            "TO": to_id,
            "CONTENT": content,
            "TOKEN": token
        })

        target_ip = to_id.split("@")[1]
        udp.sendToOne(message, target_ip)

    elif cmd == "sendfile":
        to_id = input("TO (user@ip): ")
        filepath = input("Path to file: ")

        if not os.path.exists(filepath):
            print("File not found.")
            continue

        file_id = sendFileOffer(user_id, to_id, filepath, udp)
        time.sleep(1)
        sendFileChunks(user_id, to_id, filepath, file_id, udp)

    elif cmd == "peers":
        print("Known peers:")
        for uid, name in known_peers.items():
            print(f"- {name} ({uid})")

    elif cmd == "messages":
        print("Received posts:")
        for uid, msg in received_posts:
            print(f"- {uid}: {msg}")
    
    elif cmd == "tictactoe":
        to_id = input("TO (user@ip): ")
        peer_ip = to_id.split("@")[1]
        symbol = input("Choose symbol (X or O): ").upper()
        is_first = (symbol == "X")
        playGame(user_id, peer_ip, symbol, is_first)

    elif cmd == "verbose":
        verbose_mode = not verbose_mode
        print(f"[DEBUG] Verbose mode: {verbose_mode}")

    elif cmd == "exit":
        print("Exiting")
        break

    else:
        print("Unknown command.")
    time.sleep(0.1)
