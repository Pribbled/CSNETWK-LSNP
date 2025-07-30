import socket
from constants import PORT, BUFFER, RETRY_DELAY, RETRY_LIMIT

board = [" "] * 9
acknowledged = set()
seen_moves = set()

#replace with main socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", PORT))
sock.settimeout(1)

#board display
def displayBoard():
    print("\n")
    for i in range(0, 9, 3):
        print(" " + " | ".join(board[i:i+3]))
        if i < 6:
            print("---|---|---")

#Converts text format (Fixed with AI)
def message(msg):
    data = {}
    for line in msg.strip().splitlines():
        if ": " in line:
            k, v = line.split(": ", 1)
            data[k.strip()] = v.strip()
    return data

#sends ack
def ack(id, ip):
    ack = f"TYPE: ACK\nMESSAGE_ID: {id}\nSTATUS: RECEIVED\n\n"
    sock.sendto(ack.encode(), (ip, PORT))

#5.13 Tic Tac Toe Move Format
def send_move(gameid, turn, pos, symbol, id, PeerIP):
    msg_id = f"{random.getrandbits(32):08x}"
    token = f"{my_id}|{int(time.time())+60}|game"
    msg = (
        f"TYPE: TICTACTOE_MOVE\n"
        f"FROM: {my_id}\n"
        f"TO: {peer_ip}\n"
        f"GAMEID: {gameid}\n"
        f"MESSAGE_ID: {msg_id}\n"
        f"POSITION: {pos}\n"
        f"SYMBOL: {symbol}\n"
        f"TURN: {turn}\n"
        f"TOKEN: {token}\n\n"
    )

    for attempt in range(RETRY_LIMIT):
        sock.sendto(msg.encode(), (peer_ip, PORT)) #send to Peer
        print(f"[SEND] Move {pos} (Turn {turn}) → {peer_ip} [Attempt {attempt + 1}]")
        time.sleep(RETRY_DELAY)
        if msg_id in acknowledged:
            print("[INFO] ACK received.")
            return
    print("[WARN] No ACK received, move may be lost.")

#receives msgs (TYPE: ACK/TYPE:MOVE)
def receiver(id):
    while True:
        try:
            data, addr = sock.recvfrom(BUFFER)
            msg = data.decode(errors="ignore")
            fields = message(msg)
            ip = addr[0]

            if fields.get("TYPE") == "TICTACTOE_MOVE":
                gameid = fields["GAMEID"]
                move_id = fields["MESSAGE_ID"]
                turn = fields["TURN"]
                pos = int(fields["POSITION"])
                sym = fields["SYMBOL"]

                move_key = f"{gameid}:{turn}"
                if move_key in seen_moves:
                    send_ack(move_id, ip)
                    continue

                seen_moves.add(move_key)
                send_ack(move_id, ip)
                board[pos] = sym
                print(f"\n[RECV] {sym} placed at {pos} (Turn {turn})")
                print_board()

            elif fields.get("TYPE") == "ACK":
                acknowledged.add(fields["MESSAGE_ID"])

        except socket.timeout:
            continue


#main func for gameplay
def playGame(id, PeerIP, symbol, is_first):
    #game id as stated in rfc
    gameid = "g123"
    turn = 1 if is_first else 2

    if is_first:
        print("[GAME] You go first.")
        displayBoard()
    else:
        print("[GAME] Waiting for opponent...")

    while True:
        if (turn % 2 == 1 and is_first) or (turn % 2 == 0 and not is_first):
            #own turn
            while True:
                try:
                    pos = int(input("Choose position (0-8): "))
                    if 0 <= pos <= 8 and board[pos] == " ":
                        break
                    print("Invalid or occupied cell.")
                except:
                    print("Enter a number 0-8.")

            board[pos] = symbol
            displayBoard()
            send_move(gameid, turn, pos, symbol, my_id, peer_ip)
        else:
            print(f"[WAIT] Opponent's turn {turn}...")

        turn += 1
        time.sleep(1)

if __name__ == "__main__":
    id = input("Enter your USER_ID (e.g. alice@192.168.1.11): ")
    PeerIP = input("Peer IP: ")
    symbol = input("Choose symbol (X or O): ").upper()
    is_first = (symbol == "X")

    threading.Thread(target=receiver, args=(id,), daemon=True).start()
    run_game(id, PeerIP, symbol, is_first)