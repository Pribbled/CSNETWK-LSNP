import socket
import threading

PORT = 50999
BROADCAST = '<broadcast>'

def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(('', PORT))
    return sock

class UDPHandler:
    def __init__(self, on_receive):
        self.sock = create_socket()
        self.on_receive = on_receive
        self.running = True

    def send(self, message, addr, broadcast=False):
        target = (BROADCAST if broadcast else addr, PORT)
        self.sock.sendto(message.encode('utf-8'), target)

    def listen(self):
        def loop():
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(65535)
                    self.on_receive(data.decode('utf-8'), addr)
                except:
                    continue
        threading.Thread(target=loop, daemon=True).start()
