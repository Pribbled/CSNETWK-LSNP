from message import build_message
from socket_handler import send_unicast
from state import local_profile, games, peers
from utils import generate_message_id, current_unix_timestamp

def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    sender = msg.get("FROM")
    target = msg.get("TO")
    game_id = msg.get("GAME")
    move = msg.get("MOVE")
    time = msg.get("TIME")

    if msg_type == "GAME_INVITE":
        print(f"🎮 Game invite from {sender} (Game ID: {game_id})")
        games[game_id] = {
            "players": [sender, local_profile.USER_ID],
            "board": [" "] * 9,
            "turn": sender,
        }

    elif msg_type == "GAME_MOVE":
        idx = int(move)
        if game_id in games:
            game = games[game_id]
            if game["board"][idx] == " ":
                game["board"][idx] = "X" if sender == game["players"][0] else "O"
                game["turn"] = local_profile.USER_ID  # switch turn
                display_board(game["board"])
            else:
                print(f"⚠️ Invalid move from {sender} (position {idx} already taken)")

    elif msg_type == "GAME_QUIT":
        if game_id in games:
            print(f"🚪 {sender} has quit game {game_id}")
            del games[game_id]

def display_board(board):
    print("\nTic Tac Toe:")
    for i in range(0, 9, 3):
        print(" | ".join(board[i:i+3]))
        if i < 6:
            print("---------")
    print("")

# ========== CLI ==========

def cli_game_invite():
    target_id = input("Opponent USER_ID: ").strip()
    if target_id not in peers:
        print("❌ Unknown user.")
        return

    game_id = generate_message_id()
    msg = build_message({
        "TYPE": "GAME_INVITE",
        "FROM": local_profile.USER_ID,
        "TO": target_id,
        "GAME": game_id,
        "TIME": str(current_unix_timestamp())
    })

    send_unicast(msg, peers[target_id])
    print(f"🎯 Invite sent to {target_id}. Game ID: {game_id}")

    # Initialize local game state
    games[game_id] = {
        "players": [local_profile.USER_ID, target_id],
        "board": [" "] * 9,
        "turn": local_profile.USER_ID,
    }

def cli_game_move():
    game_id = input("Game ID: ").strip()
    if game_id not in games:
        print("❌ Game not found.")
        return

    game = games[game_id]
    if game["turn"] != local_profile.USER_ID:
        print("⏳ Not your turn.")
        return

    display_board(game["board"])
    move = int(input("Your move (0–8): ").strip())
    if move < 0 or move > 8 or game["board"][move] != " ":
        print("❌ Invalid move.")
        return

    game["board"][move] = "X" if local_profile.USER_ID == game["players"][0] else "O"
    game["turn"] = game["players"][1]  # switch turn
    display_board(game["board"])

    # Send move to opponent
    opponent = game["players"][1]
    msg = build_message({
        "TYPE": "GAME_MOVE",
        "FROM": local_profile.USER_ID,
        "TO": opponent,
        "GAME": game_id,
        "MOVE": str(move),
        "TIME": str(current_unix_timestamp())
    })

    send_unicast(msg, peers[opponent])
    print(f"✅ Move sent.")

def cli_game_quit():
    game_id = input("Game ID to quit: ").strip()
    if game_id not in games:
        print("❌ Game not found.")
        return

    opponent = games[game_id]["players"][1]
    msg = build_message({
        "TYPE": "GAME_QUIT",
        "FROM": local_profile.USER_ID,
        "TO": opponent,
        "GAME": game_id,
        "TIME": str(current_unix_timestamp())
    })

    send_unicast(msg, peers[opponent])
    del games[game_id]
    print(f"🚪 You quit the game.")
