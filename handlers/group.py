from message import build_message
from socket_handler import send_udp, send_unicast
from state import group_map, peers
from utils import generate_message_id, current_unix_timestamp
from state import config

# ========== RECEIVE ==========
def handle(msg: dict, addr: tuple):
    msg_type = msg.get("TYPE", "").upper()
    group_id = msg.get("GROUP")
    user = msg.get("USER")
    content = msg.get("CONTENT", "")
    time = msg.get("TIME")

    if msg_type == "GROUP_CREATE":
        if group_id not in group_map:
            group_map[group_id] = {"members": set()}
        group_map[group_id]["members"].add(user)
        print(f"👥 Group created: {group_id} by {user}")

    elif msg_type == "GROUP_JOIN":
        if group_id not in group_map:
            group_map[group_id] = {"members": set()}
        group_map[group_id]["members"].add(user)
        print(f"➕ {user} joined group {group_id}")

    elif msg_type == "GROUP_MSG":
        if group_id in group_map and user in group_map[group_id]["members"]:
            print(f"💬 [{group_id}] {user}: {content}")
        else:
            print(f"⚠️ Message from non-member {user} in group {group_id} ignored.")

    elif msg_type == "GROUP_LEAVE":
        if group_id in group_map and user in group_map[group_id]["members"]:
            group_map[group_id]["members"].remove(user)
            print(f"👋 {user} left group {group_id}")

# ========== CLI ==========

def cli_group_create():
    group_id = input("Enter new group name: ").strip()
    if not group_id:
        print("❌ Group name cannot be empty.")
        return

    msg = build_message({
        "TYPE": "GROUP_CREATE",
        "GROUP": group_id,
        "USER": config.USER_ID,
        "TIME": str(current_unix_timestamp())
    })

    send_udp(msg)
    print(f"✅ Group '{group_id}' created.")

def cli_group_join():
    group_id = input("Enter group name to join: ").strip()
    if not group_id:
        print("❌ Group name required.")
        return

    msg = build_message({
        "TYPE": "GROUP_JOIN",
        "GROUP": group_id,
        "USER": config.USER_ID,
        "TIME": str(current_unix_timestamp())
    })

    send_udp(msg)
    print(f"✅ Join request for group '{group_id}' sent.")

def cli_group_msg():
    group_id = input("Group name: ").strip()
    if group_id not in group_map or config.USER_ID not in group_map[group_id]["members"]:
        print("❌ You are not a member of this group.")
        return

    content = input("Message: ").strip()
    if not content:
        print("❌ Message cannot be empty.")
        return

    msg = build_message({
        "TYPE": "GROUP_MSG",
        "GROUP": group_id,
        "USER": config.USER_ID,
        "TIME": str(current_unix_timestamp()),
        "CONTENT": content
    })

    # Optionally multicast to all known peers
    for peer_id, peer_ip in peers.items():
        send_unicast(msg, peer_ip)

    print("✅ Group message sent.")

def cli_group_leave():
    group_id = input("Group to leave: ").strip()
    if group_id not in group_map:
        print("❌ Group not found.")
        return

    msg = build_message({
        "TYPE": "GROUP_LEAVE",
        "GROUP": group_id,
        "USER": config.USER_ID,
        "TIME": str(current_unix_timestamp())
    })

    send_udp(msg)
    print(f"👋 Leave message sent for group '{group_id}'.")
