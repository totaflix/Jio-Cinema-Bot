


from datetime import datetime
import os
import json
import shutil
import random
import requests
from pyropatch.listen import Client as PClient, ListenerCanceled
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from bot import LOGGER
from bot.config import Config
from bot.helpers.binary_funcs import download_media, get_formats, mux_subtitle
from bot.helpers.utils import FORMAT_CODES, send_document, send_video
from bot.helpers.gdrive import gDrive
from script import Script

logger = LOGGER(__name__)
INFO = {}

@Client.on_message(
    filters.regex(r"^http?s:\/\/www\.jiocinema\.com\/(?:watch\/)?movies\/(?:.+(?:\/\d\/\d\/|\?))(?:type=\d{0,2}&id=)?([a-zA-Z0-9]+).*") 
    & filters.private
    & filters.user(Config.JIO_USERS)
)
async def handle_url(bot: Client, update: Message):
    
    m_id = update.matches[0].group(1)
    
    m = await update.reply_text(
        "Processing...⏳",
        quote=True
    )

    a = filter(lambda x: x.type == enums.MessageEntityType.URL, update.entities)
    a = list(a)
    url = update.text[a[0].offset:a[0].offset + a[0].length]

    # logger.info(f"Processing {url}")

    headers = {'os': 'Android' }
    metadata = requests.get('https://prod.media.jio.com/apis/common/v3/metamore/get/' + m_id, headers=headers).json()
    if not metadata.get('name', False):
        await m.edit(
            Script.MOVIE_NOT_FOUND,
            parse_mode=enums.ParseMode.HTML
        )
        return
    
    movie_name = metadata['name']
    movie_year = metadata['year']
    movie_lang = metadata['language']

    logger.info(f"Movie name: {movie_name},\nURL: {url}")
    try:
        sub = metadata['srt']
        mainurl = 'sldhnecdnems02.cdnsrv.jio.com'
        suburl = 'https://' + mainurl + '/jiobeats.cdn.jio.com/content/entry/data/' + str(sub)
    except:
        suburl = ""
        logger.info(f"No subtitles found for {movie_name}")
    
    thumb_url = "https://jiocinemaweb.cdn.jio.com/jioimages.cdn.jio.com/content/entry/dynamiccontent/thumbs/300/-/0/" + metadata["image"]
    _id = metadata['thumb']
    _id = _id.split('/')
    f1 = _id[1]
    f2 = _id[2]
    
    del metadata

    hls_url = 'http://jiobeats.cdn.jio.com/vod/_definst_/smil:vodpublic/' + str(f1) + '/' + str(f2) + '/' + m_id + '.smil/index.m3u8'

    stdout, stderr = await get_formats(hls_url)
    if(
        stderr and
        "nonnumeric port" not in stderr
    ):

        error_message = stderr
        try:
            await m.edit_text(
                text=Script.FORMATS_NOT_FOUND + "\n\nError:\n<code>{}</code>".format(
                    str(error_message)),
                parse_mode=enums.ParseMode.HTML
            )
        except: pass
        return False

    if stdout:

        x_reponse = stdout
        if "\n" in x_reponse:
            x_reponse, _ = x_reponse.split("\n")
        response_json = json.loads(x_reponse)
        buttons = []

        if "formats" in response_json:
            for formats in response_json["formats"]:
                format_id = formats.get("format_id", False)
                if not format_id:
                    continue

                format_idd = FORMAT_CODES.get(int(format_id), "Und") + f" ({format_id})"
                buttons.append(
                    [
                        InlineKeyboardButton("🎞️ " + format_idd, callback_data="dl_vid#jio|{}|{}".format(format_id, "video")),
                        InlineKeyboardButton("📂 " + format_idd, callback_data="dl_vid#jio|{}|{}".format(format_id, "file")),
                        InlineKeyboardButton("☁️ " + format_idd, callback_data="dl_vid#jio|{}|{}".format(format_id, "drive")),
                    ]
                )

        else:
            format_id: str = response_json["format_id"]
            buttons.append([
                InlineKeyboardButton("🎞️ " + format_idd, callback_data="dl_vid#jio|{}|{}".format(format_id, "video")),
                InlineKeyboardButton("📂 " + format_idd, callback_data="dl_vid#jio|{}|{}".format(format_id, "file")),
                InlineKeyboardButton("☁️ " + format_idd, callback_data="dl_vid#jio|{}|{}".format(format_id, "drive")),
            ])

    else:
        await m.edit_text(
            text=Script.FORMATS_NOT_FOUND,
            parse_mode=enums.ParseMode.HTML
        )
        return

    INFO[m.id] = {}
    INFO[m.id]["id"] = m_id
    INFO[m.id]["url"] = url
    INFO[m.id]["suburl"] = suburl
    INFO[m.id]["name"] = movie_name
    INFO[m.id]["year"] = movie_year
    INFO[m.id]["lang"] = movie_lang
    INFO[m.id]["thumb"] = thumb_url
    INFO[m.id]["f1"] = f1
    INFO[m.id]["f2"] = f2

    buttons.append([InlineKeyboardButton("Cancel ❌", callback_data=f"canceljio_{update.from_user.id}")])

    reply_markup = InlineKeyboardMarkup(buttons)
    try:
        await m.edit_text(
            text=Script.SELECT_FORMAT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
    except Exception as e: 
        raise e


@Client.on_callback_query(filters.regex(pattern=r"^dl_vid#jio\|(.*)\|(.*)$"))
async def dl_formats(bot: Client, update: CallbackQuery):
    user_id = update.from_user.id
    _, quality, up_mode = update.data.split("|")
    
    if not INFO.get(update.message.id, False):
        await update.answer(
            Script.OUTDATED_MSG,
            show_alert=True
        )
        await update.message.delete()
        return
    else:
        m_id = INFO[update.message.id]["id"]
        url = INFO[update.message.id]["url"]
        suburl = INFO[update.message.id]["suburl"]
        movie_name = INFO[update.message.id]["name"]
        movie_year = INFO[update.message.id]["year"]
        movie_lang = INFO[update.message.id]["lang"]
        thumb_url = INFO[update.message.id]["thumb"]
        f1 = INFO[update.message.id]["f1"]
        f2 = INFO[update.message.id]["f2"]
    
    qualityy = quality
    qualityy = FORMAT_CODES.get(int(quality), "Und")

    path = "/app/downloads/" + str(user_id) + "/" + str(update.message.reply_to_message_id) + "/"
    if not os.path.isdir(path):
        os.makedirs(path)
    name = movie_name + "." + movie_year + "." + movie_lang + "." +\
        qualityy + '.' + 'JIO' + '.' + "H.264" + "." + "AAC"

    if suburl:
        responce = requests.get(suburl)
        subtitles = True
    else:
        subtitles = False

    if subtitles and responce.status_code == 200:
        name += "." + "ESUBS" + '.mp4'
        subtitles = path + "subtitle_" + m_id + ".srt"
        with open(subtitles, 'wb+') as f:
            f.write(responce.content)
    else:
        name += '.mkv'

    cdn_domain = 'sldhnecdnems05.cdnsrv.jio.com'
    dl_url = 'https://' + cdn_domain + '/jiobeats.cdn.jio.com/content/entry/data/' + str(f1) + '/' + str(f2) + '/' + m_id + '_' + quality + '.mp4'

    try:
        await update.edit_message_text(
            Script.DOWNLOADING_CONTENT.format(name),
        )
    except:
        pass

    start_time = datetime.now()
    stdout, stderr = await download_media(dl_url, path+name, show_progress=True, update=update.message, start_time=start_time, name=name)

    if not os.path.exists(path+name):
        await update.edit_message_text(
            Script.FAILED_TO_DOWNLOAD,
        )
        logger.info(f"Failed to download {name},\n\nOutput: {stdout}\n\nError: {stderr}")
        return

    with os.scandir(path) as entries:
        for entry in entries:
            logger.info(entry.name)
    logger.info(os.path.exists(path+name))
    out, err = await mux_subtitle(path+name, path+name[:-4], subtitles)
    
    name = name[:-4] + ".mkv"

    if os.path.getsize(path+name)> 2097152000 and up_mode != "drive":
        await update.edit_message_text(
            Script.FILE_SIZE_TOO_LARGE,
        )
        up_mode = "drive"

    thumb_path = path + "thumbnail.jpg"
    if not os.path.exists(thumb_path):
        with open(thumb_path, 'wb+') as f:
            f.write(requests.get(thumb_url).content)

    if up_mode == "video":
        await send_video(bot, update.message, path+name)
    elif up_mode == "file":
        await send_document(bot, update.message, path+name)
    elif up_mode == "drive":
        gd = gDrive(bot, update.message, name)
        msg, glink, ilink, vlink = await gd.upload(name, path+name)
        buttons = [
            [InlineKeyboardButton("☁️ Drive Link", url=glink)],
        ]
        if Config.INDEX_URL:
            buttons.append([InlineKeyboardButton("⚡ Index Link", url=ilink)])
            # buttons.append([InlineKeyboardButton("🌐 View Link", url=vlink)])

        await update.message.reply(
            text=msg,
            quote=True,
            parse_mode=enums.ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply(
            text=Script.SOMETHING_WRONG,
            parse_mode=enums.ParseMode.HTML
        )
        return
    await update.message.delete()

    try:
        shutil.rmtree(path)
    except Exception as e:
        logger.error(e)
