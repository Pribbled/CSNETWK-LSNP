import threading
import random
import time
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
            print("Commands: post <message> | dm <user_id> <message> | follow <user_id> | unfollow <user_id> | exit")

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

        else:
            print("Unknown command. Type 'help'.")

