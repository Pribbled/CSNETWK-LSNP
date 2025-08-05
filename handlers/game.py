import random
from utils import generate_token, current_unix_timestamp, generate_message_id
from socket_handler import send_udp
from state import local_profile, peers
from message import build_message

# --- Game State ---
game_state = {
    "opponent": None,
    "board": [" "] * 9,
    "my_turn": False,
    "symbol": None,
    "opponent_symbol": None,
    "gameid": None,
    "turn": 0,
}

# For ACK
ack_pending = {}

def send_ack(msg_id, addr):
    ack = {
        "TYPE": "ACK",
        "MESSAGE_ID": msg_id,
        "STATUS": "RECEIVED"
    }
    send_udp(build_message(ack), addr[0])


def handle(msg, addr):
    msg_type = msg.get("TYPE")

    if msg_type == "ACK":
        msg_id = msg.get("MESSAGE_ID")
        if msg_id in ack_pending:
            del ack_pending[msg_id]
        return

    if msg_type == "TICTACTOE_INVITE":
        send_ack(msg.get("MESSAGE_ID"), addr)
        handle_invite(msg, addr)
    elif msg_type == "TICTACTOE_MOVE":
        send_ack(msg.get("MESSAGE_ID"), addr)
        handle_move(msg, addr)
    elif msg_type == "TICTACTOE_RESULT":
        send_ack(msg.get("MESSAGE_ID"), addr)
        handle_result(msg, addr)


def handle_invite(msg, addr):
    from_id = msg.get("FROM")
    to_id = msg.get("TO")
    symbol = msg.get("SYMBOL")
    gameid = msg.get("GAMEID")

    if to_id != local_profile["USER_ID"]:
        return  # Not for us

    display = peers.get(from_id, {}).get("DISPLAY_NAME", from_id)
    print(f"\n🎮 {display} is inviting you to play Tic Tac Toe as {('O' if symbol == 'X' else 'X')}.")

    choice = input("Accept? (y/n): ").strip().lower()
    if choice == "y":
        game_state["opponent"] = from_id
        game_state["board"] = [" "] * 9
        game_state["my_turn"] = False  # inviter moves first
        game_state["symbol"] = "O" if symbol == "X" else "X"
        game_state["opponent_symbol"] = symbol
        game_state["gameid"] = gameid
        game_state["turn"] = 1
        print("✅ Game accepted. Waiting for opponent’s move.")
    else:
        print("❌ Game invite rejected.")


def handle_move(msg, addr):
    from_id = msg.get("FROM")
    position = int(msg.get("POSITION", -1))
    symbol = msg.get("SYMBOL")
    turn = int(msg.get("TURN", 0))

    if game_state["opponent"] != from_id or msg.get("GAMEID") != game_state["gameid"]:
        return  # Ignore unrelated game

    if position < 0 or position > 8 or game_state["board"][position] != " ":
        print("⚠️ Invalid move received.")
        return

    game_state["board"][position] = symbol
    game_state["my_turn"] = True
    game_state["turn"] = turn + 1

    display = peers.get(from_id, {}).get("DISPLAY_NAME", from_id)
    print(f"\n🎮 {display} placed {symbol} at {position}.")
    print_board()

    if check_winner(symbol):
        send_result("LOSS", winning_line=get_winning_line(symbol))
        print("💥 You lost!")
        reset_game()
    #elif " " not in game_state["board"]:   #Draw (Not tested)
        #send_result("DRAW")
        #print("🤝 It's a draw!")
        #reset_game()

def handle_result(msg, addr):
    result = msg.get("RESULT", "UNKNOWN")
    from_id = msg.get("FROM")
    display = peers.get(from_id, {}).get("DISPLAY_NAME", from_id)

    print(f"\n🏁 Game Over — {display} reports: {result}")
    if "WINNING_LINE" in msg:
        print(f"Winning line: {msg['WINNING_LINE']}")
    reset_game()


def send_result(result_str, winning_line=None):
    if not game_state["opponent"]:
        return
    msg = {
        "TYPE": "TICTACTOE_RESULT",
        "FROM": local_profile["USER_ID"],
        "TO": game_state["opponent"],
        "GAMEID": game_state["gameid"],
        "MESSAGE_ID": generate_message_id(),
        "RESULT": result_str,
        "SYMBOL": game_state["symbol"],
        "WINNING_LINE": ",".join(map(str, winning_line)) if winning_line else "",
        "TIMESTAMP": str(current_unix_timestamp()),
    }
    peer = peers.get(game_state["opponent"])
    if peer:
        send_udp(build_message(msg), peer["ADDRESS"])


def cli_game_invite():
    to_id = input("Send invite to USER_ID: ").strip()
    peer = peers.get(to_id)
    if not peer:
        print("❌ Peer not found.")
        return

    token = generate_token(local_profile["USER_ID"], ttl=3600, scope="game")
    symbol = input("Choose your symbol (X/O): ").strip().upper()
    if symbol not in ["X", "O"]:
        print("❌ Invalid symbol. Defaulting to X.")
        symbol = "X"

    gameid = f"g{random.randint(0,255)}"
    game_state["opponent"] = to_id
    game_state["board"] = [" "] * 9
    game_state["my_turn"] = True if symbol == "X" else False
    game_state["symbol"] = symbol
    game_state["opponent_symbol"] = "O" if symbol == "X" else "X"
    game_state["gameid"] = gameid
    game_state["turn"] = 1

    msg = {
        "TYPE": "TICTACTOE_INVITE",
        "FROM": local_profile["USER_ID"],
        "TO": to_id,
        "GAMEID": gameid,
        "MESSAGE_ID": generate_message_id(),
        "SYMBOL": symbol,
        "TIMESTAMP": str(current_unix_timestamp()),
        "TOKEN": token,
    }

    send_udp(build_message(msg), peer["ADDRESS"])
    print(f"📨 Invite sent. You play as {symbol}.")


def cli_game_move():
    if not game_state["opponent"]:
        print("❌ No active game.")
        return
    if not game_state["my_turn"]:
        print("⏳ Wait for your turn.")
        return

    print_board()
    try:
        position = int(input("Enter your move (0–8): "))
        if position < 0 or position > 8 or game_state["board"][position] != " ":
            print("❌ Invalid move.")
            return
    except ValueError:
        print("❌ Please enter a number between 0–8.")
        return

    game_state["board"][position] = game_state["symbol"]
    game_state["my_turn"] = False

    to_id = game_state["opponent"]
    peer = peers.get(to_id)
    if not peer:
        print("❌ Peer not found.")
        return

    msg = {
        "TYPE": "TICTACTOE_MOVE",
        "FROM": local_profile["USER_ID"],
        "TO": to_id,
        "GAMEID": game_state["gameid"],
        "MESSAGE_ID": generate_message_id(),
        "POSITION": str(position),
        "SYMBOL": game_state["symbol"],
        "TURN": game_state["turn"],
        "TOKEN": generate_token(local_profile["USER_ID"], ttl=3600, scope="game"),
    }

    send_udp(build_message(msg), peer["ADDRESS"])
    print(f"✅ Move sent ({game_state['symbol']} at {position}).")
    print_board()

    if check_winner(game_state["symbol"]):
        send_result("WIN", winning_line=get_winning_line(game_state["symbol"]))
        print("🏆 You win!")
        reset_game()
    #elif " " not in game_state["board"]:  #Draw
        #send_result("DRAW")
        #print(" It's a draw!")
        #reset_game()

def cli_game_quit():
    print("👋 Quitting current game.")
    reset_game()


def reset_game():
    game_state.update({
        "opponent": None,
        "board": [" "] * 9,
        "my_turn": False,
        "symbol": None,
        "opponent_symbol": None,
        "gameid": None,
        "turn": 0,
    })


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
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # columns
        [0, 4, 8], [2, 4, 6]              # diagonals
    ]
    return any(all(b[i] == symbol for i in line) for line in win_positions)

def get_winning_line(symbol):
    b = game_state["board"]
    win_positions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    for line in win_positions:
        if all(b[i] == symbol for i in line):
            return line
    return []