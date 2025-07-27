import threading
import random
import time
import base64
import os
from protocol import message_types as mt
from protocol import serializer, token
from network.udp_handler import UDPHandler
from core.dispatcher import Dispatcher

def generate_message_id():
    return f"{random.getrandbits(64):x}"

class Peer:
    def __init__(self, username, ip):
        self.username = username
        self.ip = ip
        self.user_id = f"{username}@{ip}"
        self.dispatcher = Dispatcher(self)
        self.udp = UDPHandler(self.dispatcher.handle)
        self.running = True
        self.file_chunks = {}
        self.pending_file_offers = {}  # file_id -> offer message

    def broadcast_profile(self):
        msg = {
            "TYPE": mt.PROFILE,
            "USER_ID": self.user_id,
            "DISPLAY_NAME": self.username,
            "STATUS": "Online!",
        }
        self.udp.send(serializer.serialize_message(msg), addr=None, broadcast=True)

    def send_ping(self):
        msg = {
            "TYPE": mt.PING,
            "USER_ID": self.user_id
        }
        self.udp.send(serializer.serialize_message(msg), addr=None, broadcast=True)

    def _send_file(self, to_user, file_path):
        if not os.path.isfile(file_path):
            print("File not found.")
            return

        file_id = generate_message_id()
        with open(file_path, "rb") as f:
            file_data = f.read()

        encoded = base64.b64encode(file_data).decode("utf-8")
        CHUNK_SIZE = 512
        chunks = [encoded[i:i + CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]

        filename = os.path.basename(file_path)
        filesize = os.path.getsize(file_path)
        filetype = "application/octet-stream"
        ttl = 3600

        # Send FILE_OFFER
        offer = {
            "TYPE": mt.FILE_OFFER,
            "FROM": self.user_id,
            "TO": to_user,
            "FILENAME": filename,
            "FILESIZE": filesize,
            "FILETYPE": filetype,
            "FILEID": file_id,
            "DESCRIPTION": "Sent via LSNP",
            "TIMESTAMP": int(time.time()),
            "TOKEN": token.create_token(self.user_id, ttl, "file")
        }
        self.udp.send(serializer.serialize_message(offer), addr=to_user.split('@')[-1])

        # Send FILE_CHUNKs
        for i, chunk in enumerate(chunks):
            msg = {
                "TYPE": mt.FILE_CHUNK,
                "FROM": self.user_id,
                "TO": to_user,
                "FILEID": file_id,
                "CHUNK_INDEX": i,
                "TOTAL_CHUNKS": len(chunks),
                "CHUNK_SIZE": CHUNK_SIZE,
                "TOKEN": token.create_token(self.user_id, ttl, "file"),
                "DATA": chunk
            }
            self.udp.send(serializer.serialize_message(msg), addr=to_user.split('@')[-1])

    def run(self):
        self.udp.listen()
        self.broadcast_profile()
        self.send_ping()

        # Start background PING thread
        threading.Thread(target=self._auto_ping, daemon=True).start()

        print(f"LSNP peer started as {self.user_id}. Type 'help' for commands.\n")
        self._input_loop()

    def _auto_ping(self):
        while self.running:
            self.send_ping()
            time.sleep(10)

    def _input_loop(self):
        while self.running:
            try:
                cmd = input("> ").strip()
                if not cmd:
                    continue
                self._handle_command(cmd)
            except KeyboardInterrupt:
                self.running = False
                print("\nExiting...")

    def _handle_command(self, cmd):
        parts = cmd.split()
        if parts[0] == "help":
            print("Commands: post <msg>\n" \
            "dm <user_id> <msg>\n" \
            "follow <user_id>\n" \
            "unfollow <user_id>\n" \
            "sendfile <user_id>\n"
            "<file_path>\n" \
            "exit")

        elif parts[0] == "exit":
            self.running = False
            print("Goodbye!")

        elif parts[0] == "post" and len(parts) > 1:
            content = " ".join(parts[1:])
            ttl = 3600
            msg = {
                "TYPE": mt.POST,
                "USER_ID": self.user_id,
                "CONTENT": content,
                "TTL": ttl,
                "MESSAGE_ID": generate_message_id(),
                "TOKEN": token.create_token(self.user_id, ttl, "broadcast"),
            }
            self.udp.send(serializer.serialize_message(msg), addr=None, broadcast=True)

        elif parts[0] == "dm" and len(parts) > 2:
            to_user = parts[1]
            content = " ".join(parts[2:])
            ttl = 3600
            ip_only = to_user.split('@')[-1]
            msg = {
                "TYPE": mt.DM,
                "FROM": self.user_id,
                "TO": to_user,
                "CONTENT": content,
                "TIMESTAMP": int(time.time()),
                "MESSAGE_ID": generate_message_id(),
                "TOKEN": token.create_token(self.user_id, ttl, "chat"),
            }
            self.udp.send(serializer.serialize_message(msg), addr=ip_only)

        elif parts[0] == "follow" and len(parts) == 2:
            to_user = parts[1]
            ttl = 3600
            msg = {
                "TYPE": mt.FOLLOW,
                "FROM": self.user_id,
                "TO": to_user,
                "MESSAGE_ID": generate_message_id(),
                "TIMESTAMP": int(time.time()),
                "TOKEN": token.create_token(self.user_id, ttl, "follow"),
            }
            ip_only = to_user.split('@')[-1]
            self.udp.send(serializer.serialize_message(msg), addr=ip_only)

        elif parts[0] == "unfollow" and len(parts) == 2:
            to_user = parts[1]
            ttl = 3600
            msg = {
                "TYPE": mt.UNFOLLOW,
                "FROM": self.user_id,
                "TO": to_user,
                "MESSAGE_ID": generate_message_id(),
                "TIMESTAMP": int(time.time()),
                "TOKEN": token.create_token(self.user_id, ttl, "follow"),
            }
            ip_only = to_user.split('@')[-1]
            self.udp.send(serializer.serialize_message(msg), addr=ip_only)

        elif parts[0] == "sendfile" and len(parts) == 3:
            to_user = parts[1]
            file_path = parts[2]
            self._send_file(to_user, file_path)

        elif parts[0] == "acceptfile" and len(parts) == 2:
            file_id = parts[1]
            offer = self.pending_file_offers.get(file_id)
            if not offer:
                print("No such file offer.")
                return
            msg = {
                "TYPE": mt.FILE_ACCEPT,
                "FROM": self.user_id,
                "TO": offer["FROM"],
                "FILEID": file_id,
                "TIMESTAMP": int(time.time())
            }
            ip_only = offer["FROM"].split('@')[-1]
            self.udp.send(serializer.serialize_message(msg), addr=ip_only)
            print("Accepted the file offer.")

        elif parts[0] == "rejectfile" and len(parts) == 2:
            file_id = parts[1]
            offer = self.pending_file_offers.get(file_id)
            if not offer:
                print("No such file offer.")
                return
            msg = {
                "TYPE": mt.FILE_REJECT,
                "FROM": self.user_id,
                "TO": offer["FROM"],
                "FILEID": file_id,
                "TIMESTAMP": int(time.time())
            }
            ip_only = offer["FROM"].split('@')[-1]
            self.udp.send(serializer.serialize_message(msg), addr=ip_only)
            print("Rejected the file offer.")

        else:
            print("Unknown command. Type 'help'.")

