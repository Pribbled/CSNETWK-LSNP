# test_cli.py

from udp_socket import UDPSocket
from message_parsing import buildMessage, parseMessage

import time

verbose_mode = True
known_peers = {}   # {user_id: display_name}
received_posts = []  # store messages

def handle_message(raw_msg, addr):
    global verbose_mode, known_peers, received_posts
    msg = parseMessage(raw_msg)
    msg_type = msg.get("TYPE", "")

    if verbose_mode:
        print(f"\n[DEBUG] Raw: {raw_msg}")
        print(f"[DEBUG] Parsed: {msg}")

    if msg_type == "PROFILE":
        user_id = msg.get("USER_ID", addr[0])
        display_name = msg.get("DISPLAY_NAME", user_id)
        known_peers[user_id] = display_name
        print(f"👤 New peer: {display_name} ({user_id})")

    elif msg_type == "POST":
        user_id = msg.get("USER_ID", addr[0])
        content = msg.get("CONTENT", "")
        received_posts.append((user_id, content))
        print(f"📝 {user_id}: {content}")

    elif msg_type == "DM":
        sender = msg.get("FROM", addr[0])
        recipient = msg.get("TO", "")
        content = msg.get("CONTENT", "")
        print(f"💬 DM from {sender} → {recipient}: {content}")

udp = UDPSocket(verbose=True)
udp.receive(handle_message)

print("LSNP Test CLI")
print("Commands: profile, post, dm, peers, messages, verbose, exit")

while True:
    cmd = input(">>> ").strip().lower()

    if cmd == "profile":
        user_id = input("USER_ID: ")
        name = input("Display Name: ")
        status = input("Status: ")
        message = buildMessage({
            "TYPE": "PROFILE",
            "USER_ID": user_id,
            "DISPLAY_NAME": name,
            "STATUS": status
        })
        udp.sendToAll(message)

    elif cmd == "post":
        user_id = input("USER_ID: ")
        content = input("Content: ")
        message = buildMessage({
            "TYPE": "POST",
            "USER_ID": user_id,
            "CONTENT": content
        })
        udp.sendToAll(message)
    
    elif cmd == "dm":
        from_id = input("FROM (your USER_ID): ")
        to_id = input("TO (user@ip): ")
        content = input("Content: ")

        message = buildMessage({
            "TYPE": "DM",
            "FROM": from_id,
            "TO": to_id,
            "CONTENT": content
        })

        target_ip = to_id.split("@")[1]
        udp.sendToOne(message, target_ip)

    elif cmd == "peers":
        print("👥 Known peers:")
        for uid, name in known_peers.items():
            print(f"- {name} ({uid})")

    elif cmd == "messages":
        print("📜 Received posts:")
        for uid, msg in received_posts:
            print(f"- {uid}: {msg}")

    elif cmd == "verbose":
        verbose_mode = not verbose_mode
        print(f"[DEBUG] Verbose mode: {verbose_mode}")

    elif cmd == "exit":
        break

    else:
        print("Unknown command.")
    time.sleep(0.1)
