import socket
import threading
import struct
import time

PORT = 50999

def get_local_ip():
    """Detect the local IP address used to reach the internet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))  # Google's DNS server
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

def calculate_broadcast_address(ip, netmask='255.255.255.0'):
    ipaddr = struct.unpack('!I', socket.inet_aton(ip))[0]
    netmask = struct.unpack('!I', socket.inet_aton(netmask))[0]
    broadcast = ipaddr | ~netmask
    return socket.inet_ntoa(struct.pack('!I', broadcast & 0xffffffff))

def create_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind(('', PORT))  # Bind to all available interfaces
    return sock

class UDPHandler:
    def __init__(self, on_receive):
        self.sock = create_socket()
        self.on_receive = on_receive
        self.running = True
        self.local_ip = get_local_ip()
        self.broadcast_ip = calculate_broadcast_address(self.local_ip)

        print(f"[UDP] Local IP: {self.local_ip}")
        print(f"[UDP] Broadcast IP: {self.broadcast_ip}")

    def send(self, message, addr, broadcast=False):
        target_ip = self.broadcast_ip if broadcast else addr
        target = (target_ip, PORT)
        try:
            self.sock.sendto(message.encode('utf-8'), target)
            print(f"[UDP] Sent to {target_ip}:{PORT}\n{message}\n")
        except Exception as e:
            print(f"[UDP] Failed to send to {target_ip}:{PORT} — {e}")

    def listen(self):
        def loop():
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(65535)
                    message = data.decode('utf-8')
                    print(f"[UDP] Received from {addr}:\n{message}\n")
                    self.on_receive(message, addr)
                except Exception as e:
                    print(f"[UDP] Receive error: {e}")
        threading.Thread(target=loop, daemon=True).start()
