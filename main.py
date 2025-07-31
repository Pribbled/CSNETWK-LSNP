import threading
from socket_handler import create_socket, receive_udp
from message import parse_message
from state import seen_message_ids
from utils import current_unix_timestamp
from config import VERBOSE
from handlers import (
    profile,
    post,
    ping,
    dm,
    file_transfer,
    group,
    game,
    like,
    token,
    follow,
)

import sys


def log(msg: str):
    if VERBOSE:
        print(f"[LOG] {msg}")

# def dispatch_message(msg: dict, addr: tuple, sock):
#     msg_type = msg.get("TYPE", "").upper()
    
#     if VERBOSE:
#         print(f"[{current_unix_timestamp()}] < {addr[0]}:{addr[1]} | TYPE: {msg_type}")

#     try:
#         data, addr = receive_udp(sock)
#         msg = parse_message(data)
#         msg_id = msg.get("Message-ID")

#         if msg_id and msg_id in seen_message_ids:
#             continue  # Skip duplicate messages
#         if msg_id:
#             seen_message_ids.add(msg_id)

#         msg_type = msg.get("Type")
#         if not msg_type:
#             continue

#         if msg_type == "PROFILE":
#             profile.handle(msg, addr)
#         elif msg_type == "POST":
#             post.handle(msg, addr)
#         elif msg_type == "DM":
#             dm.handle(msg, addr)
#         elif msg_type.startswith("FILE_"):
#             file_transfer.handle(msg, addr)
#         elif msg_type.startswith("GROUP_"):
#             group.handle(msg, addr)
#         elif msg_type.startswith("GAME_"):
#             game.handle(msg, addr)
#         elif msg_type == "TOKEN":
#             token.handle(msg, addr)
#         elif msg_type == "FOLLOW":
#             follow.handle(msg, addr)
#         elif msg_type == "UNFOLLOW":
#             follow.handle(msg, addr)
#         else:
#             if VERBOSE:
#                 print(f"⚠️  Unknown message type: {msg_type}")
#     except Exception as e:
#         log(f"Receive error: {e}")

def dispatch_message(msg: dict, addr: tuple, sock):
    msg_type = msg.get("TYPE", "").upper()

    if VERBOSE:
        print(f"[{current_unix_timestamp()}] < {addr[0]}:{addr[1]} | TYPE: {msg_type}")

    msg_id = msg.get("ID")
    if msg_id and msg_id in seen_message_ids:
        return
    if msg_id:
        seen_message_ids.add(msg_id)

    if msg_type == "PROFILE":
        profile.handle(msg, addr)
    elif msg_type == "POST":
        post.handle(msg, addr)
    elif msg_type == "LIKE":
        like.handle(msg, addr)
    elif msg_type == "DM":
        dm.handle(msg, addr)
    elif msg_type == "PING":
        ping.handle(msg, addr)
    elif msg_type.startswith("FILE"):
        file_transfer.handle(msg, addr)
    elif msg_type.startswith("GROUP"):
        group.handle(msg, addr)
    elif msg_type.startswith("GAME"):
        game.handle(msg, addr)
    elif msg_type == "TOKEN":
        token.handle(msg, addr)
    elif msg_type == "FOLLOW":
        follow.handle(msg, addr)
    elif msg_type == "UNFOLLOW":
        follow.handle(msg, addr)
    else:
        if VERBOSE:
            print(f"⚠️  Unknown message type: {msg_type}")
    
def receive_loop():
    sock = create_socket()
    while True:
        try:
            data, addr = receive_udp(sock)
            # print(f"\nRaw Incoming:\n{data}")
            msg = parse_message(data)
            # print("Parsed Message:\n", msg)
            dispatch_message(msg, addr, sock)
        except Exception as e:
            if VERBOSE:
                print(f"❌ Receive error: {e}")

def cli_loop():
    print("🎛️  LSNP CLI Ready. Type 'help' for commands.")
    while True:
        try:
            cmd = input("LSNP> ").strip()
            if cmd == "exit":
                break
            elif cmd == "help":
                print("""
Available Commands:
- profile     Send PROFILE update
- post        Broadcast a POST
- dm          Send a direct message
- follow      Follow a user
- file        Send a FILE_OFFER
- group       Manage groups (create, join, leave)
- game        Send a GAME_MOVE or GAME_INVITE
- revoke      Revoke a token
- unfollow    Unfollow a user
- verbose     Toggle verbose mode
- exit        Quit the program
                """)
            elif cmd == "profile":
                profile.cli_send()
            elif cmd == "post":
                post.cli_send()
            elif cmd == "dm":
                dm.cli_send()
            elif cmd == "ping":
                ping.cli_send()
            elif cmd == "file":
                file_transfer.cli_send()
            elif cmd == "group":
                group.cli_send()
            elif cmd == "group-create":
                group.cli_group_create()
            elif cmd == "group-join":
                group.cli_group_join()
            elif cmd == "group-msg":
                group.cli_group_msg()
            elif cmd == "group-leave":
                group.cli_group_leave()
            elif cmd == "game":
                game.cli_send()
            elif cmd == "game-invite":
                game.cli_game_invite()
            elif cmd == "game-move":
                game.cli_game_move()
            elif cmd == "game-quit":
                game.cli_game_quit()
            elif cmd == "follow":
                follow.cli_follow()
            elif cmd == "unfollow":
                follow.cli_unfollow()
            elif cmd == "revoke":
                token = input("Token to revoke: ").strip()
                from token import revoke_token
                revoke_token(token)
                print("✅ Token revoked.")
            elif cmd == "verbose":
                import config
                config.VERBOSE = not config.VERBOSE
                print(f"Verbose mode {'ON' if config.VERBOSE else 'OFF'}")
            else:
                print("❓ Unknown command. Try 'help'.")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    from state import local_profile
    from utils import get_local_ip  # if you modularize this later

    username = input("Enter your LSNP username: ").strip()
    # local_profile["Name"] = username  # optional, if using as DISPLAY_NAME
    local_profile["USER_ID"] = f"{username}@{local_profile['LOCAL_IP']}"

    print(f"Logging in as {username}@{local_profile['LOCAL_IP']}\n")
    threading.Thread(target=receive_loop, daemon=True).start()
    ping.start_auto_ping()
    cli_loop()