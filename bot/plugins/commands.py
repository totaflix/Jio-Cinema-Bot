


import math
import requests
import asyncio
import time
import shutil
import psutil
import sys
import os

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from bot import LOGGER, Config
from bot.helpers import humanbytes
from bot.database.database import Database
from script import Script


logger = LOGGER(__name__)
db = Database()


@Client.on_message(filters.command(["start"]))
async def start (bot, update):
    
    await update.reply_text(
        Script.START_TEXT.format(update.from_user.mention), 
        True, 
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Help", callback_data="help"),
                ]
            ]
        )
    )


@Client.on_message(filters.command(["help"]))
async def help (bot, update):
        
    await update.reply_text(
        Script.HELP_TEXT, 
        True, 
        parse_mode=enums.ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("Start", callback_data="start"),
                    InlineKeyboardButton("About", callback_data="about"),
                ]
            ]
        )
    )   


@Client.on_message(filters.command(["about"]))
async def about (bot, update):

        await update.reply_text(
            Script.ABOUT_TEXT, 
            True, 
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Start", callback_data="start"),
                        InlineKeyboardButton("Help", callback_data="help"),
                    ]
                ]
            )
        )

@Client.on_message(filters.command(["stats"]))
async def stats (bot, update):
    if update.from_user.id not in Config.AUTH_USERS:
        return
    else:
        stats = await db.get_all_users_count()
        await update.reply_text(
            "Total Users: {}".format(stats), 
            True, 
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Start", callback_data="start"),
                        InlineKeyboardButton("Help", callback_data="help"),
                    ]
                ]
            )
        )


@Client.on_message(filters.private & filters.command(["status"]) & filters.user(Config.AUTH_USERS))
async def stats(bot, update):

    currentTime = time.strftime("%Hh%Mm%Ss", time.gmtime(
        time.time() - Config.BOT_START_TIME))
    total, used, free = shutil.disk_usage(".")
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage('/').percent


    ms_g = f"<b><u>Bot Status</b></u>\n" \
        f"<code>Uptime: {currentTime}</code>\n"\
        f"<code>CPU Usage: {cpu_usage}%</code>\n"\
        f"<code>RAM Usage: {ram_usage}%</code>\n\n" \
        f"<code>Total Disk Space: {total}</code>\n" \
        f"<code>Used Space: {used} ({disk_usage}%)</code>\n" \
        f"<code>Free Space: {free}</code>\n"
        

    msg = await bot.send_message(
        chat_id=update.chat.id,
        text="__Processing...__",
        parse_mode=enums.ParseMode.MARKDOWN
    )
    await msg.edit_text(
        text=ms_g,
        parse_mode=enums.ParseMode.HTML
    )


@Client.on_message(filters.private & filters.command(["restart"]) & filters.user(Config.AUTH_USERS))
async def restart(bot, update):

    b = await bot.send_message(
        chat_id=update.chat.id,
        text="__Restarting.....__",
        parse_mode=enums.ParseMode.MARKDOWN
    )
    await asyncio.sleep(3)
    await b.delete()
    if Config.HEROKU_API_KEY and Config.HEROKU_APP_NAME:
        heroku = heroku3.from_key(Config.HEROKU_API_KEY)
        heroku_app = heroku.apps()[Config.HEROKU_APP_NAME]
        heroku_app.restart()
    
    os.remove("logs.txt")
    shutil.rmtree("/app/downloads/" , ignore_errors=True)
    if os.path.exists(".git"):
        os.system("git pull")
    os.execl(sys.executable, sys.executable, "-m", "bot")


@Client.on_message(filters.command(['logs']) & filters.user(Config.AUTH_USERS))
async def send_logs(_, m):
    await m.reply_document(
        "logs.txt",
        caption='Logs'
    )
    
