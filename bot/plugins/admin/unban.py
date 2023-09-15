

import traceback
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from . import Config, User, LOGGER


logger = LOGGER(__name__)
db = User()


@Client.on_message(filters.private & filters.command("unban_user") & filters.user(Config.AUTH_USERS), -1)
async def unban(bot: Client, update: Message):

    if len(update.command) == 1:
        await update.reply_text(
            "Use this command to unban any user.\n\nUsage:\n\n`/unban_user user_id`\n\n"
            "Eg: `/unban_user 1234567`\n This will unban user with id `1234567`.",
            quote=True,
        )
        return

    try:
        user_id = int(update.command[1])
        unban_log_text = f"Unbanning user {user_id}"

        try:
            await bot.send_message(user_id, "Your ban was lifted!")
            unban_log_text += "\n\nUser notified successfully!"
        except Exception as e:
            logger.debug(e, exc_info=True)
            unban_log_text += (
                f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
            )

        data = await db.get_ban_status(user_id)
        data['is_banned'] = False
        data['ban_reason'] = ""
        data['ban_duration'] = 0

        await db.update_ban_status(user_id, data)

        logger.debug(unban_log_text)
        await update.reply_text(unban_log_text, quote=True, parse_mode=enums.ParseMode.MARKDOWN)
    except Exception as e:
        logger.error(e, exc_info=True)
        await update.reply_text(
            f"Error occoured! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
