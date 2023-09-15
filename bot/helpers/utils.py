

import os
import time
import requests

from pyrogram import (
    Client, 
    StopTransmission,
    utils,
    enums
)
from pyrogram.types import (
    Message, 
    CallbackQuery, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from pyrogram.raw import *
from pyrogram.errors import FilePartMissing

from PIL import Image
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

from bot.config import Config
from bot.database.database import Database
from bot.plugins import LOGGER
from bot.helpers.progress import Progress
from bot import LOGGER


logger = LOGGER(__name__)
db = Database()


FORMAT_CODES = {
    18192: "2160p.HQ",
    15192: "2160p.L", 
    12192: "1080p.HD", 
    9192: "1080p.HQ2",
    8192: "1080p.HQ",
    8128: "1080p.M3",
    6192: "1080p.M2",
    6128: "1080p.M1",
    4192: "1080p.L",
    4128: "1080p.L2",
    3128: "1080p.L1",
    2492: "720p.HQ",
    2428: "720.H2",
    1728: "720.H",
    1328: "720p.L", 
    896: "480p.M", 
    864: "480p.L",
    696: "360p", 
    464: "240p.H",
    448: "240p.H2",
    300: "240p.M", 
    248: "240p.L",
    232: "240p.L2",
    184: "144p",
    132: "130p.HQ", 
    112: "130p.L", 
}


async def get_thumb(user_id: int, message_id: int):

    path = "/app/downloads/" + str(user_id) + f'/{message_id}' + "/thumbnail.jpg"

    if not os.path.exists(path):
        res = requests.get(Config.DEFAULT_THUMB)
        with open(path, "wb+") as f:
            f.write(res.content)

    width = 0
    height = 0
    if path is not None:
        metadata = extractMetadata(createParser(path))
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")
        Image.open(path).convert("RGB").save(path)
        img = Image.open(path)
        img.resize((90, height))
        img.save(path, "JPEG")

    return path


async def send_document(bot: Client, update: Message, path: str):

    thumb_path = await get_thumb(update.reply_to_message.from_user.id, update.reply_to_message_id)
    start_time = time.time()
    prog = Progress(update.reply_to_message.from_user.id, bot, update)
    await bot.send_document(
        chat_id=update.chat.id,
        document=path,
        thumb=thumb_path,
        reply_to_message_id=update.id,
        progress=prog.progress_for_pyrogram,
        progress_args=(
            "Uploading Started..!",
            start_time
        )
    )


async def send_video(bot: Client, update: Message, path: str):

    thumb = await get_thumb(update.reply_to_message.from_user.id,  update.reply_to_message_id)
    start_time = time.time()
    prog = Progress(update.reply_to_message.from_user.id, bot, update)

    width = 0
    height = 0
    duration = 0
    metadata = extractMetadata(createParser(path))
    if metadata is not None:
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
        if metadata.has("width"):
            width = metadata.get("width")
        if metadata.has("height"):
            height = metadata.get("height")

    thumb = await bot.save_file(thumb)
    file = await bot.save_file(
        path,
        progress=prog.progress_for_pyrogram,
        progress_args=('Uploading Started', start_time)
    )

    media = types.InputMediaUploadedDocument(
        mime_type="video/mp4",
        file=file,
        thumb=thumb,
        attributes=[
            types.DocumentAttributeVideo(
                supports_streaming=True,
                duration=duration,
                w=width,
                h=height
            ),
            types.DocumentAttributeFilename(
                file_name=os.path.basename(path))
        ]
    )

    try:
        while True:
            try:
                r = await bot.invoke(
                    functions.messages.SendMedia(
                        peer=await bot.resolve_peer(update.chat.id),
                        media=media,
                        reply_to_msg_id=update.reply_to_message.id,
                        random_id=bot.rnd_id(),
                        **await utils.parse_text_entities(bot, '', enums.ParseMode.HTML, None)
                    )
                )
            except FilePartMissing as e:
                await bot.save_file(path, file_id=file.id, file_part=e.x)
            else:
                for i in r.updates:
                    if isinstance(i, (types.UpdateNewMessage,
                                      types.UpdateNewChannelMessage,
                                      types.UpdateNewScheduledMessage)):
                        return await Message._parse(
                            bot, i.message,
                            {i.id: i for i in r.users},
                            {i.id: i for i in r.chats},
                            is_scheduled=isinstance(
                                i, types.UpdateNewScheduledMessage)
                        )
    except StopTransmission:
        return None


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s") if seconds else "0s")
    return tmp



