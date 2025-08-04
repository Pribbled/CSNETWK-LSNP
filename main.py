import threading
from socket_handler import create_socket, receive_udp
from message import parse_message
from state import seen_message_ids
from utils import current_unix_timestamp
from config import settings
from handlers import (
    ack,
    profile,
    post,
    ping,
    dm,
    group,
    game,
    like,
    token,
    revoke,
    follow,
)
from file_transfer import cli
from file_transfer.receiver import (
    handle_file_offer, 
    handle_file_chunk, 
    handle_file_received, 
    handle_file_accept
)
from handlers.token import revoke_token, revoke_all_tokens_by_user

def log(msg: str):
    if settings["VERBOSE"]:
        print(f"[LOG] {msg}")

def toggle_verbose():
    settings["VERBOSE"] = not settings["VERBOSE"]
    print(f"{'🔊 Verbose ON' if settings['VERBOSE'] else '🔈 Verbose OFF'}")

def dispatch_message(msg: dict, addr: tuple, sock):
    msg_type = msg.get("TYPE", "").upper()

    if settings["VERBOSE"]:
        print(f"[{current_unix_timestamp()}] < {addr[0]}:{addr[1]} | TYPE: {msg_type}")

    msg_id = msg.get("ID")
    if msg_id and msg_id in seen_message_ids:
        return
    if msg_id:
        seen_message_ids.add(msg_id)

    if msg_type == "ACK":
        ack.handle(msg, addr)
    elif msg_type == "PROFILE":
        profile.handle(msg, addr)
    elif msg_type == "POST":
        post.handle(msg, addr)
    elif msg_type == "LIKE":
        like.handle(msg, addr)
    elif msg_type == "DM":
        dm.handle(msg, addr)
    elif msg_type == "PING":
        ping.handle(msg, addr)
    elif msg_type == "FILE_OFFER":
        handle_file_offer(msg)
    elif msg_type == "FILE_CHUNK":
        handle_file_chunk(msg)
    elif msg_type == "FILE_RECEIVED":
        handle_file_received(msg)
    elif msg_type == "FILE_ACCEPT":
        handle_file_accept(msg)
    elif msg_type.startswith("GROUP"):
        group.handle(msg, addr)
    elif msg_type.startswith("GAME"):
        game.handle(msg, addr)
    elif msg_type == "TICTACTOE_INVITE":
        game.handle_invite(msg, addr)
    elif msg_type == "TICTACTOE_MOVE":
        game.handle_move(msg, addr)
    elif msg_type == "TICTACTOE_RESULT":
        game.handle_result(msg, addr)
     #elif msg_type == "GAME_QUIT":
        #handle_game_quit(msg, addr)
    elif msg_type == "TOKEN":
        token.handle(msg, addr)
    elif msg_type == "REVOKE":
        revoke.handle(msg, addr)
    elif msg_type == "FOLLOW":
        follow.handle(msg, addr)
    elif msg_type == "UNFOLLOW":
        follow.handle(msg, addr)
    else:
        if settings["VERBOSE"]:
            print(f"⚠️  Unknown message type: {msg_type}")
    
def receive_loop():
    sock = create_socket()
    while True:
        try:
            data, addr = receive_udp(sock)
            if settings["VERBOSE"] : print("\n============== Raw Incoming ===============\n", data)
            msg = parse_message(data)
            if settings["VERBOSE"] : print("============== Parsed Message ==============\n", msg)
            dispatch_message(msg, addr, sock)
        except Exception as e:
            if settings["VERBOSE"]:
                print(f"❌ Receive error: {e}")

def cli_loop():
    print("🎛️  LSNP CLI Ready. Type 'help' for commands.")
    while True:
        try:
            cmd = input("LSNP> ").strip()
            if cmd == "exit":
                try:
                    sock = create_socket()
                    # revoke_token(sock)
                    revoke.revoke_all_tokens_by_user()
                except Exception as e:
                    print(f"⚠️  Error sending REVOKE: {e}")
                break
            elif cmd == "help":
                print("""
Available Commands:
- profile     Send PROFILE update
- post        Broadcast a POST
- like        Like a POST
- dm          Send a direct message
- follow      Follow a user
- file        Send a FILE_OFFER
- group       Manage groups (create, join, leave)
- game        Play Tic Tac Toe (invite, move, quit)
- revoke      Revoke a token
- unfollow    Unfollow a user
- verbose     Toggle verbose mode
- exit        Quit the program
                """)
            elif cmd == "profile":
                profile.cli_send()
            elif cmd == "post":
                post.cli_send()
            elif cmd == "like":
                like.cli_send()
            elif cmd == "dm":
                dm.cli_send()
            elif cmd == "ping":
                ping.cli_send()
            elif cmd == "file":
                cli.file_transfer_cli()
            elif cmd == "group":
                print("""
                                Group Commands:
                                - create    Create a Group
                                - update    Update a Group (add/remove members)
                                - message   Send a message to your group
                                - list      List groups you belong to
                                - members   Show group members
                                - leave     Leave a group
                                                    """)
                sub_cmd = input("group> ").strip()
                if sub_cmd == "create":
                    group.cli_group_create()
                elif sub_cmd == "update":
                    group.cli_group_update()
                elif sub_cmd == "message":
                    group.cli_group_msg()
                elif sub_cmd == "list":
                    group.cli_group_list()
                elif sub_cmd == "members":
                    group.cli_group_members()
                elif sub_cmd == "leave":
                    group.cli_group_leave()
                else:
                    print("❓ Unknown group command.")
            elif cmd == "group-create":
                group.cli_group_create()
            elif cmd == "group-join":
                group.cli_group_join()
            elif cmd == "group-msg":
                group.cli_group_msg()
            elif cmd == "group-leave":
                group.cli_group_leave()
            elif cmd == "game":
                print("""
                Game commands:
                - invite   Invite someone to Tic Tac Toe
                - move     Play a Tic Tac Toe move
                - quit     Quit a Tic Tac Toe game
                    """)
                sub_cmd = input("game> ").strip()
                if sub_cmd == "invite":
                    game.cli_game_invite()
                elif sub_cmd == "move":
                    game.cli_game_move()
                elif sub_cmd == "quit":
                    game.cli_game_quit()
                else:
                    print("❓ Unknown game command. Options: invite, move, quit")
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
                token_str = input("Token to revoke: ").strip()
                revoke_token(token_str)
                print("✅ Token revoked.")
            elif cmd == "verbose":
                toggle_verbose()
            else:
                print("❓ Unknown command. Try 'help'.")
        except KeyboardInterrupt:
            try:
                sock = create_socket()
                revoke.revoke_all_tokens_by_user()
            except Exception as e:
                print(f"⚠️  Error sending REVOKE: {e}")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    from state import local_profile
    # from utils import get_local_ip  # if you modularize this later

    username = input("Enter your LSNP username: ").strip()
    # local_profile["Name"] = username  # optional, if using as DISPLAY_NAME
    local_profile["USER_ID"] = f"{username}@{local_profile['LOCAL_IP']}"

    print(f"Logging in as {username}@{local_profile['LOCAL_IP']}\n")
    threading.Thread(target=receive_loop, daemon=True).start()
    ping.start_auto_ping()
    print("Please set up your profile first!")
    cli_loop()