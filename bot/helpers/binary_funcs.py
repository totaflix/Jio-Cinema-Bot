

import os
import re
import asyncio
import datetime
from bot import LOGGER
from pyrogram import enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, MessageNotModified

currentFile = __file__
realPath = os.path.realpath(currentFile)
dirPath = os.path.dirname(realPath)
dirName = os.path.basename(dirPath)


mp4decryptexe = dirPath + '/binaries/mp4decrypt_new.exe'
# mkvmergeexe = dirPath + '/binaries/mkvmerge.exe'
aria2cexe = dirPath + '/binaries/aria2c.exe'


logger = LOGGER(__name__)
cList = []


async def execute(cmds: list, update: Message = None, show_progress=False, **kwargs):

    process = await asyncio.create_subprocess_exec(
        *cmds,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        limit=1024 * 128 # 128KiB
    )
    if update and show_progress:
        await asyncio.gather(
            read_stdout(process, update, aria2c=("aria2c" in cmds), **kwargs),
        )
    # else:
    #     logger.info("Else part: " + str(cmds))

    stdout, stderr = await process.communicate()
    stdout, stderr = stdout.decode(), stderr.decode()
    return stdout, stderr


async def get_formats(url: str):

    cmd = [
        'yt-dlp',
        '--no-warnings',
        '--allow-unplayable-formats',
        '--no-check-certificate',
        '-j',
        url
    ]

    stdout, stderr = await execute(cmd)
    return stdout, stderr


async def download_media(url: str, path: str, **kwargs):
    cmd = [
        'yt-dlp',
        '--no-warnings',
        '--quiet',
        '--external-downloader',
        'aria2c',
        # '--max-connection-per-server 10',
        # '10',
#         '--external-downloader-args',
#         '--async-dns false'
        '--progress',
        '--newline',
        '--allow-unplayable-formats',
        '--no-check-certificate',
        url,
        '-o',
        path
    ]
    stdout, stderr = await execute(cmd, **kwargs)
    return stdout, stderr


async def mux_subtitle(path: str, output: str, subtitle: str):

    cmd = [
        'mkvmerge',
        '--output',
        output + '.mkv',
        '--language', 
        '0:eng',
        '--default-track',
        '0:yes',
        '--compression',
        '0:none',
        path,
        '--language',
        '0:eng',
        '--track-order',
        '0:0,1:0,2:0,3:0,4:0',
        # '--title',
        # 'DRAWIZ',
        subtitle
    ]
    if not subtitle:
        cmd.pop()

    stdout, stderr = await execute(cmd)
    try:
        os.remove(path+output+".mp4")
        os.remove(subtitle)
    except Exception:
        pass
    return stdout, stderr



async def read_stdout(process, update: Message, **kwargs):
    
    stdout: asyncio.StreamReader = process.stdout

    if kwargs.get('start_time', False):
        start_time = kwargs.get('start_time')
    else:
        start_time = datetime.datetime.now()
    name = kwargs.get('name', 'File')
    pid = process.pid

    while True:
        now = datetime.datetime.now()
        diff = (now - start_time).seconds

        if pid in cList:
            await update.edit_text(
                "Downloading cancelled by user"
            )
            process.terminate()
            cList.remove(pid)
            return

        if round(float(diff) % float(5)) == 0:
            buf = await stdout.readline()
            if not buf:
                break
            buf = buf.replace(b'\n', b'').replace(b'\r', b'')
            buf = buf.decode()
            if not kwargs.get('aria2c', False):
                regex = re.match(
                    r"\[download\]\s+(\d{1,2}\.\d%)\s+of\s+(\d+\.\d{2}[KMGT]iB)\s+at\s+(\d+\.\d{2}[KMGT]iB\/s)\s+ETA\s+(\d+:\d+)",
                    buf
                )
            else:
                regex = re.match(
                    r"\[#(?:.+)\s(\d+(?:\.\d)?[KMGT]iB)\/(\d+(?:\.\d)?[KMGT]iB)\((\d+%)\)\sCN:\d+\sDL:(\d+B|\d+[KMGT]iB)\sETA:(.+)\]",
                    buf
                )

            if not regex:
                continue

            status = 'Downloading'
            if not kwargs.get('aria2c', False):
                percentage = regex.group(1)
                total = regex.group(2)
                speed = regex.group(3)
                eta = regex.group(4)
                current = ""
            else:
                current = regex.group(1)
                total = regex.group(2)
                percentage = regex.group(3)
                speed = regex.group(4)
                eta = regex.group(5)

            try:
                await update.edit_text(
                    f"<i>Status:</i> <code>{status}</code>\n"
                    f"<i>Name:</i> <code>{name}</code>\n"
                    "" if not kwargs.get('aria2c', False) else f"<i>Current:</i> <code>{current}</code>\n"
                    f"<i>Total:</i> <code>{total} ({percentage})</code>\n"
                    f"<i>Speed:</i> <code>{speed}</code>\n"
                    f"<i>ETA:</i> <code>{eta}</code>",
                    parse_mode=enums.ParseMode.HTML,
                    disable_web_page_preview=True,
                    reply_markup=InlineKeyboardMarkup(
                        [[
                            InlineKeyboardButton("Cancel", callback_data=f"cancel_shell#{pid}")
                        ]]
                    )
                )
            except MessageNotModified:
                pass
            except FloodWait as e:
                await asyncio.sleep(e.value)
            except Exception as e:
                logger.exception(e, exc_info=True)
