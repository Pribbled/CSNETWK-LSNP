from core.peer import Peer
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run LSNP peer.")
    parser.add_argument("--username", required=True)
    parser.add_argument("--ip", required=True)
    args = parser.parse_args()

    peer = Peer(args.username, args.ip)
    peer.run()

if __name__ == "__main__":
    main()
