

import datetime
import traceback
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from . import Config, User, LOGGER


logger = LOGGER(__name__)
db = User()


@Client.on_message(filters.private & filters.command("ban_user") & filters.user(Config.AUTH_USERS), -1)
async def ban(bot: Client, update: Message):

    if len(update.command) <= 2:
        await update.reply_text(
            "Use this command to ban any user from the bot.\n\nUsage:\n\n`/ban_user user_id "
            "ban_duration ban_reason`\n\nEg: `/ban_user 1234567 28 You misused me.`\n This will "
            "ban user with id `1234567` for `28` days for the reason `You misused me`.",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    try:
        user_id = int(update.command[1])
        ban_duration = int(update.command[2])
        ban_reason = " ".join(update.command[3:]) if len(update.command) >= 3 else ""
        
        ban_log_text = f"Banning user {user_id} for {ban_duration} day(s)" +\
                        (f" for the reason {ban_reason}." if ban_reason else ".")

        text =  f"You are banned to use this bot for **{ban_duration}** day(s) " + \
                (f"for the reason __{ban_reason}__ " if ban_reason else ".") +\
                "\n\n**Message from the admin**"

        try:
            await bot.send_message(
                user_id,
                text,
                enums.ParseMode.MARKDOWN
            )
            ban_log_text += "\n\nUser notified successfully!"

        except Exception as e:
            logger.debug(e, exc_info=True)
            ban_log_text += (
                f"\n\nUser notification failed! \n\n`{traceback.format_exc()}`"
            )

        data = await db.get_ban_status(user_id)
        
        data['is_banned'] = True
        data['banned_on'] = datetime.date.today().isoformat()
        data['ban_reason'] = ban_reason
        data['ban_duration'] = ban_duration
    
        await db.update_ban_status(user_id, data)
        await update.reply_text(ban_log_text, quote=True, parse_mode=enums.ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(e, exc_info=True)
        await update.reply_text(
            f"Error occoured! Traceback given below\n\n`{traceback.format_exc()}`",
            quote=True,
            parse_mode=enums.ParseMode.MARKDOWN
        )
