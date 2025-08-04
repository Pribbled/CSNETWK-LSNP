from message import build_message
from socket_handler import send_unicast
from state import local_profile, games, peers
from utils import generate_message_id, current_unix_timestamp
import time

ack_pending = {}

def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    sender = msg.get("FROM")
    game_id = msg.get("GAMEID")
    message_id = msg.get("MESSAGE_ID")

    if msg_type == "ACK":
        if message_id in ack_pending:
            del ack_pending[message_id]
        return

    if msg_type == "TICTACTOE_INVITE":
        symbol = msg.get("SYMBOL", "X")
        print(f"{sender} is inviting you to play tic-tac-toe.")
        games[game_id] = {
            "players": [sender, local_profile["USER_ID"]],
            "board": [" "] * 9,
            "turn": sender,
            "symbol": {
                sender: symbol,
                local_profile["USER_ID"]: "O" if symbol == "X" else "X"
            },
            "moves": set()
        }
        send_ack(message_id, addr)

    elif msg_type == "TICTACTOE_MOVE":
        position = int(msg.get("POSITION", -1))
        turn = int(msg.get("TURN", -1))

        if game_id in games:
            game = games[game_id]
            if (game_id, turn) in game["moves"]:
                send_ack(message_id, addr)
                return
            game["moves"].add((game_id, turn))

            if 0 <= position <= 8 and game["board"][position] == " ":
                symbol = msg.get("SYMBOL", "?")
                game["board"][position] = symbol
                game["turn"] = local_profile["USER_ID"]
                display_board(game["board"])
                send_ack(message_id, addr)

                result, line = check_winner(game["board"])
                if result:
                    send_result(game_id, sender, result, line, symbol)
            else:
                print(f"⚠ Invalid move from {sender}")
        else:
            print(f"❌ Unknown game {game_id}")

    elif msg_type == "TICTACTOE_RESULT":
        result = msg.get("RESULT")
        symbol = msg.get("SYMBOL")
        line = msg.get("WINNING_LINE")
        print("🎯 Game Over:", result, "by", symbol)
        display_board(games[game_id]["board"] if game_id in games else [" "] * 9)
        if game_id in games:
            del games[game_id]

# ----- Helpers -----

def send_ack(message_id, addr):
    ack_msg = {
        "TYPE": "ACK",
        "MESSAGE_ID": message_id,
        "STATUS": "RECEIVED"
    }
    send_unicast(build_message(ack_msg), addr[0], addr[1])

def check_winner(board):
    lines = [(0,1,2),(3,4,5),(6,7,8),
             (0,3,6),(1,4,7),(2,5,8),
             (0,4,8),(2,4,6)]
    for a, b, c in lines:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return "WIN", (a, b, c)
    if " " not in board:
        return "DRAW", None
    return None, None

def display_board(board):
    print("\nTic Tac Toe:")
    for i in range(0, 9, 3):
        print(" | ".join(board[i:i+3]))
        if i < 6:
            print("---------")
    print("")

# ----- CLI -----

def cli_game_invite():
    target_id = input("Opponent USER_ID: ").strip()
    if target_id not in peers:
        print("❌ Unknown user.")
        return

    game_id = "g" + str(len(games) + 1)
    symbol = "X"
    msg_id = generate_message_id()

    msg = {
        "TYPE": "TICTACTOE_INVITE",
        "FROM": local_profile["USER_ID"],
        "TO": target_id,
        "GAMEID": game_id,
        "MESSAGE_ID": msg_id,
        "SYMBOL": symbol,
        "TIMESTAMP": str(current_unix_timestamp()),
        "TOKEN": f"{local_profile['USER_ID']}|{current_unix_timestamp()+3600}|game"
    }

    retry_send(build_message(msg), target_id, msg_id)

    games[game_id] = {
        "players": [local_profile["USER_ID"], target_id],
        "board": [" "] * 9,
        "turn": local_profile["USER_ID"],
        "symbol": {
            local_profile["USER_ID"]: "X",
            target_id: "O"
        },
        "moves": set()
    }

def cli_game_move():
    game_id = input("Game ID: ").strip()
    if game_id not in games:
        print("❌ Game not found.")
        return

    game = games[game_id]
    if game["turn"] != local_profile["USER_ID"]:
        print("⏳ Not your turn.")
        return

    display_board(game["board"])
    position = int(input("Your move (0–8): ").strip())
    if position < 0 or position > 8 or game["board"][position] != " ":
        print("❌ Invalid move.")
        return

    symbol = game["symbol"][local_profile["USER_ID"]]
    game["board"][position] = symbol
    game["turn"] = next(p for p in game["players"] if p != local_profile["USER_ID"])
    display_board(game["board"])

    msg_id = generate_message_id()
    msg = {
        "TYPE": "TICTACTOE_MOVE",
        "FROM": local_profile["USER_ID"],
        "TO": game["turn"],
        "GAMEID": game_id,
        "MESSAGE_ID": msg_id,
        "POSITION": str(position),
        "SYMBOL": symbol,
        "TURN": str(len(game["moves"]) + 1),
        "TOKEN": f"{local_profile['USER_ID']}|{current_unix_timestamp()+3600}|game"
    }

    retry_send(build_message(msg), game["turn"], msg_id)

    result, line = check_winner(game["board"])
    if result:
        send_result(game_id, game["turn"], result, line, symbol)

def cli_game_quit():
    game_id = input("Game ID to quit: ").strip()
    if game_id not in games:
        print("❌ Game not found.")
        return

    opponent = next(p for p in games[game_id]["players"] if p != local_profile["USER_ID"])
    msg = {
        "TYPE": "TICTACTOE_RESULT",
        "FROM": local_profile["USER_ID"],
        "TO": opponent,
        "GAMEID": game_id,
        "MESSAGE_ID": generate_message_id(),
        "RESULT": "FORFEIT",
        "SYMBOL": games[game_id]["symbol"][local_profile["USER_ID"]],
        "WINNING_LINE": "",
        "TIMESTAMP": str(current_unix_timestamp())
    }

    send_unicast(build_message(msg), peers[opponent]["ADDRESS"])
    del games[game_id]
    print(f"🚪 You quit game {game_id} (forfeit).")

def send_result(game_id, target, result, line, symbol):
    msg = {
        "TYPE": "TICTACTOE_RESULT",
        "FROM": local_profile["USER_ID"],
        "TO": target,
        "GAMEID": game_id,
        "MESSAGE_ID": generate_message_id(),
        "RESULT": result,
        "SYMBOL": symbol,
        "WINNING_LINE": ",".join(map(str, line)) if line else "",
        "TIMESTAMP": str(current_unix_timestamp())
    }
    send_unicast(build_message(msg), peers[target]["ADDRESS"])

# ----- Retry Logic -----

def retry_send(msg_str, target_id, msg_id):
    addr = peers[target_id]["ADDRESS"]
    ack_pending[msg_id] = {"msg": msg_str, "addr": addr, "retries": 0}

    for _ in range(3):
        if msg_id not in ack_pending:
            break
        send_unicast(msg_str, addr)
        time.sleep(2)
        ack_pending[msg_id]["retries"] += 1

    if msg_id in ack_pending:
        print(f"⚠ No ACK received for {msg_id} after 3 retries.")
        del ack_pending[msg_id]