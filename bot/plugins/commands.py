


import math
import heroku3
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

    if Config.HEROKU_API_KEY:
        server = heroku3.from_key(Config.HEROKU_API_KEY)
        user_agent = (
            'Mozilla/5.0 (Linux; Android 10; SM-G975F) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/80.0.3987.149 Mobile Safari/537.36'
        )
        accountid = server.account().id
        headers = {
            'User-Agent': user_agent,
            'Authorization': f'Bearer {Config.HEROKU_API_KEY}',
            'Accept': 'application/vnd.heroku+json; version=3.account-quotas',
        }
        path = "/accounts/" + accountid + "/actions/get-quota"
        request = requests.get("https://api.heroku.com" + path, headers=headers)
        if request.status_code == 200:
            result = request.json()
            total_quota = result['account_quota']
            quota_used = result['quota_used']
            quota_left = total_quota - quota_used
            total1 = math.floor(total_quota/3600)
            used1 = math.floor(quota_used/3600)
            hours = math.floor(quota_left/3600)
            days = math.floor(hours/24)
            usedperc = math.floor(quota_used / total_quota * 100)
            leftperc = math.floor(quota_left / total_quota * 100)

    ms_g = f"<b><u>Bot Status</b></u>\n" \
        f"<code>Uptime: {currentTime}</code>\n"\
        f"<code>CPU Usage: {cpu_usage}%</code>\n"\
        f"<code>RAM Usage: {ram_usage}%</code>\n\n" \
        f"<code>Total Disk Space: {total}</code>\n" \
        f"<code>Used Space: {used} ({disk_usage}%)</code>\n" \
        f"<code>Free Space: {free}</code>\n"

    if Config.HEROKU_API_KEY:
        msg += f"<b><u>Heroku Status</b></u>\n\n" \
            f"<code>Total Dyno Hours: {total1} hrs</code>\n" \
            f"<code>Used This Month: {used1} hrs ({usedperc}%)</code>\n" \
            f"<code>Remaining This Month: {hours} hrs ({leftperc}%)</code>\n" \
            f"<code>Approximate Working Days: {days} days</code>\n"
        

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
    
