import socket
import threading
from constants import PORT, VERBOSE, BROADCAST_IP

class UDPSocket:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", PORT))

    #for broadcasting messages to everyone
    def sendToAll(self, message: str):
        if VERBOSE:
            print(f"SEND > {message}")
        self.sock.sendto(message.encode('utf-8'), (BROADCAST_IP, PORT))

    #for direct messages
    def sendToOne(self, message: str, ip: str):
        if VERBOSE:
            print(f"SEND > {message}")
        self.sock.sendto(message.encode('utf-8'), (ip, PORT))

    #for receiving messages
    def receive(self, handler):
        def listen():
            while True:
                try:
                    data, addr = self.sock.recvform(BUFFER)
                    handler(data.decode('utf-8'), addr)
                except Exception as e:
                    print(e)
        threading.Thread(target = listen, daemon = True).start()
