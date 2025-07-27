from core.peer import Peer
import socket
import argparse

def main():
    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))  # google public dns
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"  # fallback

    username = input("Enter your username (e.g., alice): ").strip()
    ip_address = get_local_ip()
    user_id = f"{username}@{ip_address}"
    print(f"Detected local IP: {ip_address}")

    peer = Peer(username, ip_address)
    peer.run()

if __name__ == "__main__":
    main()
