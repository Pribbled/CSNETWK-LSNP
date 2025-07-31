import socket
from constants import PORT, BUFFER


def addressLog ():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", PORT)) #Listens for msgs on the specified port

    print(f"Address Log for Port {PORT}:")

    while True:
        data, address = sock.recvfrom(BUFFER) #stores message and ip
        ip, port = address #Splits address into segments
        log = data.decode('utf-8', errors='Ignore').strip() #Uses UTF-8 as specified by Specs

    print(f"Received from {ip}:{port}")
    print("\n")
    print(log)
    print("\n")

    if __name__ == "__main__":
        try:
            addressLog()
        except KeyboardInterrupt:
            print("\n Log End")