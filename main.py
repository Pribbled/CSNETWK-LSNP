from udp_socket import UDPSocket
import time

def handle_message(msg, addr):
    print(f"Message from {addr[0]}: {msg}")

udp = UDPSocket(verbose=True)
udp.receive(handle_message)

print("UDP socket is running. Type messages to broadcast them.")

while True:
    msg = input(">>> ")
    if msg.lower() == "exit":
        break
    udp.sendToAll(msg)
    time.sleep(0.1)
