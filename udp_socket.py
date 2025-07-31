import socket
import threading
from constants import PORT, BUFFER, IP

class UDPSocket:
    def __init__(self, verbose = True):
        self.verbose = verbose
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", PORT))

        if self.verbose:
            print(f"Socket bound to port {PORT}")

    def sendToAll(self, msg: str):
        data = msg.encode("utf-8")
        self.sock.sendto(data, (IP, PORT))
        if self.verbose:
            print(f"Message sent to all: {msg}")

    def sendToOne(self, msg: str, target: str):
        data = msg.encode("utf-8")
        self.sock.sendto(data, (target, PORT))
        if self.verbose:
            print(f"[UDP] Unicast sent to {target}: {msg}")

    def receive(self, hndl):
        def listen():
            while True:
                try:
                    data, addr = self.sock.recvfrom(BUFFER)
                    msg = data.decode("utf-8")
                    if self.verbose:
                        print(f"Received from {addr[0]}: {msg}")
                    hndl(msg, addr)
                except Exception as e:
                    print(f"Receive error: {e}")

        threading.Thread(target = listen, daemon = True).start()