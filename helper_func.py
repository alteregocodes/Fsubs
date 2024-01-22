import asyncio
import base64
import re

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant

from config import ADMINS, FORCE_SUB_CHANNEL, FORCE_SUB_GROUP, FORCE_SUB_CHANNEL_2, FORCE_SUB_GROUP_2


async def subschannel(filter, client, update):
    if not FORCE_SUB_CHANNEL and not FORCE_SUB_CHANNEL_2:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        member2 = await client.subschannel2(chat_id=FORCE_SUB_CHANNEL_2, user_id=user_id)
    except UserNotParticipant:
        return False

    return (
        member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
        or member2.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    )


async def subsgroup(filter, client, update):
    if not FORCE_SUB_GROUP and not FORCE_SUB_GROUP_2:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member = await client.get_chat_member(chat_id=FORCE_SUB_GROUP, user_id=user_id)
        member2 = await client.subsgroup2(chat_id=FORCE_SUB_GROUP_2, user_id=user_id)
    except UserNotParticipant:
        return False

    return (
        member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
        or member2.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    )


async def is_subscribed(filter, client, update):
    if not FORCE_SUB_CHANNEL and not FORCE_SUB_CHANNEL_2:
        return True
    if not FORCE_SUB_GROUP and not FORCE_SUB_GROUP_2:
        return True
    user_id = update.from_user.id
    if user_id in ADMINS:
        return True
    try:
        member_channel = await client.get_chat_member(chat_id=FORCE_SUB_CHANNEL, user_id=user_id)
        member_channel2 = await client.subschannel2(chat_id=FORCE_SUB_CHANNEL_2, user_id=user_id)
    except UserNotParticipant:
        return False
    try:
        member_group = await client.get_chat_member(chat_id=FORCE_SUB_GROUP, user_id=user_id)
        member_group2 = await client.subsgroup2(chat_id=FORCE_SUB_GROUP_2, user_id=user_id)
    except UserNotParticipant:
        return False

    return (
        member_channel.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
        or member_channel2.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
        or member_group.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
        or member_group2.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]
    )


async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = base64_bytes.decode("ascii").rstrip("=")
    return base64_string


async def decode(base64_string):
    base64_string = base64_string + "=" * (4 - len(base64_string) % 4)
    base64_bytes = base64_string.encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string


async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages: total_messages + 200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id, message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id, message_ids=temb_ids
            )
        except BaseException:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages


async def get_message_id(client, message):
    if (
        message.forward_from_chat
        and message.forward_from_chat.id == client.db_channel.id
    ):
        return message.forward_from_message_id
    elif message.forward_from_chat or message.forward_sender_name or not message.text:
        return 0
    else:
        pattern = "https://t.me/(?:c/)?(.*)/(\\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        elif channel_id == client.db_channel.username:
            return msg_id


subsgc = filters.create(subsgroup)
subsch = filters.create(subschannel)
subsall = filters.create(is_subscribed)
