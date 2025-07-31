import socket
from config import PORT, BUFFER_SIZE, BROADCAST_ADDRESS

def create_socket() -> socket.socket:
    """Creates and binds a UDP socket to listen for messages."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.bind(('', PORT))
    return sock

def send_udp(message: str, ip: str, port: int = PORT):
    """Sends a message via UDP to a specific IP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.sendto(message.encode('utf-8'), (ip, port))
    sock.close()

def receive_udp(sock: socket.socket) -> tuple[str, tuple[str, int]]:
    """Receives a UDP message and returns decoded text and sender address."""
    data, addr = sock.recvfrom(BUFFER_SIZE)
    print (data.decode('utf-8'), addr)
    return data.decode('utf-8'), addr

def send_unicast(message: str, ip: str, port: int = None):
    """
    Sends a unicast UDP message to the specified IP and port.
    """
    port = port or PORT
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.sendto(message.encode(), (ip, port))