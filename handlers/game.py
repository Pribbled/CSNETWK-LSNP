# handlers/game.py

from utils import generate_token, current_unix_timestamp
from socket_handler import send_udp
from state import local_profile, peers
from message import build_message

# --- Game State (simple in-memory store) ---
game_state = {
    "opponent": None,
    "board": [" "] * 9,
    "my_turn": False,
}


def handle(msg, addr):
    msg_type = msg.get("TYPE")
    if msg_type == "GAME_INVITE":
        handle_invite(msg, addr)
    elif msg_type == "GAME_MOVE":
        handle_move(msg, addr)
    elif msg_type == "GAME_RESULT":
        handle_result(msg, addr)


def handle_invite(msg, addr):
    from_id = msg.get("FROM")
    to_id = msg.get("TO")
    token = msg.get("TOKEN")
    timestamp = msg.get("TIMESTAMP")

    if to_id != local_profile["USER_ID"]:
        return  # Not for us

    display = peers.get(from_id, {}).get("DISPLAY_NAME", from_id)
    print(f"\n🎮 {display} has invited you to play Tic Tac Toe.")
    choice = input("Accept? (y/n): ").strip().lower()
    
    if choice == "y":
        game_state["opponent"] = from_id
        game_state["board"] = [" "] * 9
        game_state["my_turn"] = False  # inviter goes first
        print("✅ Game accepted. Waiting for opponent’s move.")
    else:
        print("❌ Game invite rejected.")


def handle_move(msg, addr):
    from_id = msg.get("FROM")
    move_index = int(msg.get("MOVE", -1))

    if game_state["opponent"] != from_id:
        return  # ignore move from unrelated peer

    if move_index < 0 or move_index > 8:
        print("⚠️ Invalid move received.")
        return

    game_state["board"][move_index] = "X"
    game_state["my_turn"] = True

    display = peers.get(from_id, {}).get("DISPLAY_NAME", from_id)
    print(f"\n🎮 {display} made a move.")
    print_board()

    if check_winner("X"):
        send_result("LOSS")  # opponent won
        print("💥 You lost!")
        reset_game()


def handle_result(msg, addr):
    result = msg.get("RESULT", "UNKNOWN")
    from_id = msg.get("FROM")
    display = peers.get(from_id, {}).get("DISPLAY_NAME", from_id)

    print(f"\n🏁 Game Over — {display} reports: {result}")
    reset_game()


def send_result(result_str):
    if not game_state["opponent"]:
        return
    msg = {
        "TYPE": "GAME_RESULT",
        "FROM": local_profile["USER_ID"],
        "TO": game_state["opponent"],
        "RESULT": result_str,
        "TIMESTAMP": str(current_unix_timestamp()),
    }
    send_udp(build_message(msg), local_profile["LOCAL_IP"])


def cli_game_invite():
    to_id = input("Send invite to USER_ID: ").strip()
    token = generate_token(local_profile["USER_ID"], ttl=3600, scope="game")

    msg = {
        "TYPE": "GAME_INVITE",
        "FROM": local_profile["USER_ID"],
        "TO": to_id,
        "TIMESTAMP": str(current_unix_timestamp()),
        "TOKEN": token,
    }

    send_udp(build_message(msg), local_profile["LOCAL_IP"])
    game_state["opponent"] = to_id
    game_state["board"] = [" "] * 9
    game_state["my_turn"] = True
    print("📨 Invite sent. You go first!")


def cli_game_move():
    if not game_state["opponent"]:
        print("❌ No active game.")
        return
    if not game_state["my_turn"]:
        print("⏳ Wait for your turn.")
        return

    print_board()
    try:
        move = int(input("Enter your move (0–8): "))
        if move < 0 or move > 8 or game_state["board"][move] != " ":
            print("❌ Invalid move.")
            return
    except ValueError:
        print("❌ Please enter a number between 0–8.")
        return

    game_state["board"][move] = "O"
    game_state["my_turn"] = False

    msg = {
        "TYPE": "GAME_MOVE",
        "FROM": local_profile["USER_ID"],
        "TO": game_state["opponent"],
        "MOVE": str(move),
        "TIMESTAMP": str(current_unix_timestamp()),
    }
    send_udp(build_message(msg), local_profile["LOCAL_IP"])
    print("✅ Move sent.")
    print_board()

    if check_winner("O"):
        send_result("WIN")
        print("🏆 You win!")
        reset_game()


def cli_game_quit():
    print("👋 Quitting current game.")
    reset_game()


def reset_game():
    game_state["opponent"] = None
    game_state["board"] = [" "] * 9
    game_state["my_turn"] = False


def print_board():
    b = game_state["board"]
    print(f"""
     {b[0]} | {b[1]} | {b[2]} 
    ---+---+---
     {b[3]} | {b[4]} | {b[5]} 
    ---+---+---
     {b[6]} | {b[7]} | {b[8]} 
    """)


def check_winner(symbol):
    b = game_state["board"]
    win_positions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # cols
        [0, 4, 8], [2, 4, 6]              # diagonals
    ]
    return any(all(b[i] == symbol for i in line) for line in win_positions)
