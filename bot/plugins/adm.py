

from bot import LOGGER
import time
import datetime
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from . import Config, User
from bot.bot import Bot

logger = LOGGER(__name__)
db = User()

@Client.on_message((filters.regex(r"https?://.*") | filters.command(["start"]))& filters.private, -3)
async def _(c: Bot, m: Message):

    chat_id = m.from_user.id

    if Config.FORCE_SUB_CHANNEL:
        try:
            user = await c.get_chat_member(Config.FORCE_SUB_CHANNEL, chat_id)
            
            if user.status == (enums.ChatMemberStatus.BANNED):
                await m.reply_text("You are **B A N N E D**....\n", quote=True)
                return m.stop_propagation()
            
        except UserNotParticipant:
            await m.reply_text(
                text="Unauzthorized Access Detected! You need to join my channel to use me.",
                reply_markup=InlineKeyboardMarkup([
                    [   
                        InlineKeyboardButton
                            (
                                text="↗ Channel ↗", url=f"https://t.me/{Config.FORCE_SUB_CHANNEL}"
                            )
                    ]
                ])
            )
            return m.stop_propagation()
        
        except Exception as e:
            logger.info(e)
            await m.reply_text("Something Wrong. Contact My Admin", quote=True)
            return m.stop_propagation()

    if chat_id in Config.AUTH_USERS:
        data = await db.get_status(chat_id)
        if data['last_used_on'] != datetime.date.today().isoformat():
            data['last_used_on'] = datetime.date.today().isoformat()
            await db.update_status(chat_id, data, m.from_user.first_name, m.from_user.username)

        await m.continue_propagation()


    # if (tym := int(time.time()) - c.CHAT_DELAY[chat_id]) < Config.REQUEST_DELAY:
    #     await m.reply(f'Chat Flood Limit Applied...!\nPlease wait {Config.REQUEST_DELAY - tym}s before next attempt...!')
    #     return await m.stop_propagation()

    # c.CHAT_DELAY[chat_id] = int(time.time())
    await db.get_user(chat_id)


    ban_status = await db.get_ban_status(chat_id)

    if ban_status["is_banned"]:
        if (
            datetime.date.today() - datetime.date.fromisoformat(ban_status["banned_on"])
        ).days > ban_status["ban_duration"]:

            data = await db.get_ban_status(chat_id)
            data['is_banned'] = False
            data['ban_reason'] = ""
            data['ban_duration'] = 0
    
            await db.update_ban_status(chat_id, data)
        else:
            await m.reply(
                f"You are banned from using this bot!\n"
                f"Reason: {ban_status['ban_reason']}\n"
                f"Banned on: {ban_status['banned_on']}\n"
                f"""Duration: {ban_status['ban_duration'] - 
                (datetime.date.today() - datetime.date.fromisoformat(ban_status['banned_on'])).days}
                """
            )
            return await m.stop_propagation()

    data = await db.get_status(chat_id)
    if data['last_used_on'] != datetime.date.today().isoformat():
        data['last_used_on'] = datetime.date.today().isoformat()
        await db.update_status(chat_id, data, m.from_user.first_name, m.from_user.username)

    await m.continue_propagation()

