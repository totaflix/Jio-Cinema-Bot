from bot.config import Config
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram import Client, filters, enums

from script import Script


@Client.on_callback_query(filters.regex(r"start"))
async def start_cb(bot, update: CallbackQuery):
    await update.message.edit(
        Script.START_TEXT,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Help", callback_data="help"),
                ]
            ]
        )
    )
    await update.answer()

@Client.on_callback_query(filters.regex(r"^help$"))
async def help_button(bot: Client, update: CallbackQuery):

    await bot.edit_message_text(
        text=Script.HELP_TEXT,
        chat_id=update.from_user.id,
        message_id=update.message.id,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start", "start"), InlineKeyboardButton("About", "about")],
            [InlineKeyboardButton('❌ Close', 'close')]
        ]
        )
    )
    await update.answer()


@Client.on_callback_query(filters.regex(r"^about$"))
async def about_button(bot: Client, update: CallbackQuery):
    
    await bot.edit_message_text(
        text=Script.ABOUT_TEXT,
        chat_id=update.from_user.id,
        message_id=update.message.id,
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Start", "start"), InlineKeyboardButton('Help', 'help')],
            [InlineKeyboardButton('❌ Close', 'close')]
        ]
        )
    )
    await update.answer()


@Client.on_callback_query(filters.regex(r"^close$"))
async def close_button(bot: Client, update: CallbackQuery):
    await update.message.delete()
    await update.answer()


@Client.on_callback_query(filters.regex(r"^cancel\/\d+\/\d+\/\d+"), 2)
async def cancel_media_transfer(bot: Client, update: CallbackQuery):

    from bot.helpers.progress import cDict
  
    _, chat_id, msg_id, from_user = update.data.split("/")
    chat_id, msg_id, from_user = int(chat_id), int(msg_id), int(from_user)

    if (update.from_user.id == from_user) or (update.from_user.id in Config.AUTH_USERS):
        await update.answer("Cancelling...")
        cDict[chat_id] = []
        cDict[chat_id].append(msg_id)
    else:
        await update.answer("Feck U", True)
        

@Client.on_callback_query(filters.regex(r"^cancel_shell#\d+"), 2)
async def cancel_media_transfer(bot: Client, update: CallbackQuery):

    from bot.helpers.binary_funcs import cList

    _, pid = update.data.split("#")
    pid= int(pid)
    await update.answer("Cancelling...")
    cList.append(pid)


