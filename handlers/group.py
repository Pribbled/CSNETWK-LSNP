from message import build_message
from socket_handler import send_udp, send_unicast
from state import group_map, local_profile, peers
from utils import (
    current_unix_timestamp,
    generate_message_id,
    parse_csv,
    validate_token,
    generate_token,
)
from config import BROADCAST_ADDRESS
import random
from handlers import ack
from config import settings

def handle(msg, addr):
    msg_type = msg.get("TYPE", "").upper()

    if msg_type == "GROUP_CREATE":
        if not validate_token(msg.get("TOKEN", ""), "group"):
            print("❌ Invalid token for GROUP_CREATE")
            return
        handle_group_create(msg)

    elif msg_type == "GROUP_UPDATE":
        if not validate_token(msg.get("TOKEN", ""), "group"):
            print("❌ Invalid token for GROUP_UPDATE")
            return
        handle_group_update(msg)

    elif msg_type == "GROUP_MESSAGE":
        if not validate_token(msg.get("TOKEN", ""), "group"):
            print("❌ Invalid token for GROUP_MESSAGE")
            return
        handle_group_message(msg, addr)

def handle_group_create(msg):
    group_id = msg["GROUP_ID"]
    group_name = msg["GROUP_NAME"]
    members = parse_csv(msg["MEMBERS"])
    group_map[group_id] = {
        "name": group_name,
        "members": members
    }

    if local_profile["USER_ID"] in members:
        if settings["VERBOSE"]:
            print(f"📩 You have been added by {msg['FROM']} to group \"{group_name}\" ({group_id})\nMembers: {members}")
        else:
            print(f"You have been added to {group_name}")

def handle_group_update(msg):
    group_id = msg["GROUP_ID"]
    if group_id not in group_map:
        print("⚠️ Group not found")
        return

    adds = parse_csv(msg.get("ADD", ""))
    removes = parse_csv(msg.get("REMOVE", ""))

    for user in adds:
        if user not in group_map[group_id]["members"]:
            group_map[group_id]["members"].append(user)
    for user in removes:
        if user in group_map[group_id]["members"]:
            group_map[group_id]["members"].remove(user)

    if settings["VERBOSE"]:
        print(f"🔧 GROUP_UPDATE for {group_id} → +{adds} | -{removes}")
    else:
        print(f"The group \"{group_id}\" member list was updated.")

def handle_group_message(msg, addr=None):
    group_id = msg["GROUP_ID"]
    if group_id not in group_map:
        return

    sender = msg["FROM"]
    content = msg["CONTENT"]
    if settings["VERBOSE"]:
        print(f"📨 GROUP_MESSAGE from {sender} in {group_id} → {content}")
    else:
        print(f"{sender} sent “{content}”")

    if addr and "MESSAGE_ID" in msg:
        ack.send_ack(sender, msg["MESSAGE_ID"])

def auto_generate_group_id():
    return f"grp{random.randint(1000, 9999)}"

def cli_group_create():
    group_name = input("Enter Group Name: ").strip()
    members = input("Comma-separated user_ids (including yourself): ").strip()

    group_id = auto_generate_group_id()
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(local_profile["USER_ID"], "group", ttl, timestamp)

    message = build_message({
        "TYPE": "GROUP_CREATE",
        "FROM": local_profile["USER_ID"],
        "GROUP_ID": group_id,
        "GROUP_NAME": group_name,
        "MEMBERS": members,
        "TIMESTAMP": timestamp,
        "TOKEN": token,
        "MESSAGE_ID": generate_message_id(),
    })

    send_udp(message, BROADCAST_ADDRESS)

def cli_group_update():
    group_name = input("Group Name to update: ").strip()
    group_id = next((gid for gid, data in group_map.items() if data.get("name") == group_name and local_profile["USER_ID"] in data.get("members", [])), None)
    if not group_id:
        print("⚠️ You are not a member of this group.")
        return

    add = input("User(s) to add (comma-separated): ").strip()
    remove = input("User(s) to remove (comma-separated): ").strip()
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(local_profile["USER_ID"], "group", ttl, timestamp)

    message = build_message({
        "TYPE": "GROUP_UPDATE",
        "FROM": local_profile["USER_ID"],
        "GROUP_ID": group_id,
        "ADD": add,
        "REMOVE": remove,
        "TIMESTAMP": timestamp,
        "TOKEN": token,
        "MESSAGE_ID": generate_message_id(),
    })

    for user_id in group_map[group_id]["members"]:
        if user_id == local_profile["USER_ID"]:
            continue
        addr = peers.get(user_id, {}).get("ADDRESS")
        if addr:
            send_unicast(message, addr)

def cli_group_msg():
    group_name = input("Group Name to message: ").strip()
    group_id = next((gid for gid, data in group_map.items() if data.get("name") == group_name and local_profile["USER_ID"] in data.get("members", [])), None)
    if not group_id:
        print("⚠️ You are not a member of this group.")
        return

    content = input("Message: ").strip()
    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(local_profile["USER_ID"], "group", ttl, timestamp)

    members = group_map[group_id].get("members", [])
    for user_id in members:
        if user_id == local_profile["USER_ID"]:
            continue

        addr = peers.get(user_id, {}).get("ADDRESS")
        if addr:
            message = build_message({
                "TYPE": "GROUP_MESSAGE",
                "FROM": local_profile["USER_ID"],
                "GROUP_ID": group_id,
                "CONTENT": content,
                "TIMESTAMP": timestamp,
                "TOKEN": token,
                "MESSAGE_ID": generate_message_id(),
            })
            send_unicast(message, addr)

def cli_group_list():
    print("\nGroups you belong to:")
    for group_id, data in group_map.items():
        if local_profile["USER_ID"] in data.get("members", []):
            print(f"- {group_id} ({data['name']})")

def cli_group_leave():
    group_name = input("Group Name to leave: ").strip()
    group_id = next((gid for gid, data in group_map.items() if data.get("name") == group_name and local_profile["USER_ID"] in data.get("members", [])), None)

    if not group_id:
        print("⚠️ You are not a member of this group.")
        return

    timestamp = current_unix_timestamp()
    ttl = 3600
    token = generate_token(local_profile["USER_ID"], "group", ttl, timestamp)

    message = build_message({
        "TYPE": "GROUP_UPDATE",
        "FROM": local_profile["USER_ID"],
        "GROUP_ID": group_id,
        "REMOVE": local_profile["USER_ID"],
        "TIMESTAMP": timestamp,
        "TOKEN": token,
        "MESSAGE_ID": generate_message_id(),
    })

    for user_id in group_map[group_id]["members"]:
        if user_id == local_profile["USER_ID"]:
            continue
        addr = peers.get(user_id, {}).get("ADDRESS")
        if addr:
            send_unicast(message, addr)

    group_map[group_id]["members"].remove(local_profile["USER_ID"])
    print(f"🚪 You have left the group '{group_map[group_id]['name']}'")

def cli_group_members():
    group_name = input("Group Name: ").strip()
    group_id = next((gid for gid, data in group_map.items() if data.get("name") == group_name and local_profile["USER_ID"] in data.get("members", [])), None)

    if not group_id:
        print("⚠️ Group not found or you are not a member.")
        return
    print(f"\nMembers of {group_id} ({group_map[group_id]['name']}):")
    for member in group_map[group_id]["members"]:
        print(f"- {member}")
