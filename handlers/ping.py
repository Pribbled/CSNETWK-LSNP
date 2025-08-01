from state import local_profile
from socket_handler import send_unicast, send_udp
from message import build_message
from config import settings, PING_INTERVAL, BROADCAST_ADDRESS
import time
import threading

def build_ping():
    return build_message({
        "TYPE": "PING",
        "USER_ID": local_profile["USER_ID"],
        "NAME": local_profile.get("NAME", ""),
        "STATUS": local_profile.get("STATUS", "")
    })

# CLI-invoked PING command
def cli_send():
    if not local_profile.get("USER_ID"):
        print("❌ Cannot send PING (no local profile set).")
        return

    msg = build_ping()
    send_udp(msg, BROADCAST_ADDRESS)

    if settings["VERBOSE"]:
        print("📡 Sent PING broadcast.")

# Respond to received PING
def handle(msg: dict, addr: tuple):
    if msg.get("TYPE", "").upper() != "PING":
        return

    if not local_profile.get("USER_ID"):
        if settings["VERBOSE"]:
            print("⚠️  Ignored PING (no local profile set).")
        return

    fields = {
        "TYPE": "PROFILE",
        "USER_ID": local_profile["USER_ID"],
        "NAME": local_profile.get("NAME", ""),
        "AVATAR_TYPE": local_profile.get("AVATAR_TYPE", "text/emoji"),
        "AVATAR_ENCODING": local_profile.get("AVATAR_ENCODING", "utf-8"),
        "AVATAR_DATA": local_profile.get("AVATAR_DATA", ""),
        "STATUS": local_profile.get("STATUS", "")
    }

    response = build_message(fields)
    send_unicast(response, addr[0])

    if settings["VERBOSE"]:
        print(f"📤 Responded to PING with PROFILE to {addr[0]}")

# Auto PING loop (daemon thread)
def auto_ping_loop():
    while True:
        if not local_profile.get("USER_ID"):
            time.sleep(PING_INTERVAL)
            continue

        msg = build_ping()
        if settings["VERBOSE"]:
            print("📡 Broadcasting PING...")
        send_udp(msg, BROADCAST_ADDRESS)
        time.sleep(PING_INTERVAL)

def start_auto_ping():
    t = threading.Thread(target=auto_ping_loop, daemon=True)
    t.start()
