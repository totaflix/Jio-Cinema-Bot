

import io
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from . import Config, User, LOGGER


logger = LOGGER(__name__)
db = User()

@Client.on_message(filters.private & filters.command("banned_users") & filters.user(Config.AUTH_USERS), -1)
async def banned_users(_: Client, update: Message):

    all_banned_users = await db.get_all_banned_users()
    banned_usr_count = 0
    text = ""
    for banned_user in all_banned_users:
        user_id = banned_user["_id"]
        ban_duration = banned_user["ban_status"]["ban_duration"]
        banned_on = banned_user["ban_status"]["banned_on"]
        ban_reason = banned_user["ban_status"]["ban_reason"]
        banned_usr_count += 1
        text += f"> **user_id**: `{user_id}`, **Ban Duration**: `{ban_duration}`, **Banned on**: "\
        f"`{banned_on}`, **Reason**: `{ban_reason}`\n\n"
    reply_text = f"Total banned user(s): `{banned_usr_count}`\n\n{text}"

    if len(reply_text) > 4096:
        banned_usrs = io.BytesIO()
        banned_usrs.name = "banned-users.txt"
        banned_usrs.write(reply_text.encode())
        await update.reply_document(banned_usrs, True)
        return
    await update.reply_text(reply_text, True, enums.ParseMode.MARKDOWN)

