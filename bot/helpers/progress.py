

import os
import math
import asyncio
import time

from pyrogram import Client, enums
from pyrogram.types import(
  InlineKeyboardButton, 
  InlineKeyboardMarkup, 
  Message
)
from pyrogram.errors import FloodWait
from bot.helpers import LOGGER, Config

cDict = {}
logger = LOGGER(__name__)


class Progress:
    def __init__(self, from_user, client, mess: Message, drive=False):
        self._from_user = from_user
        self._client = client
        self._mess = mess
        self._cancelled = False
        self._drive = drive

    @property
    def is_cancelled(self):
        chat_id = self._mess.chat.id
        mes_id = self._mess.id
        if cDict.get(chat_id, False) and mes_id in cDict[chat_id]:
            self._cancelled = True
        return self._cancelled

    async def progress_for_pyrogram(self, current, total, ud_type, start):

        chat_id = self._mess.chat.id
        mes_id = self._mess.id
        from_user = self._from_user
        now = time.time()
        diff = now - start

        if self.is_cancelled:

            await self._mess.edit(
                f"<i>Sucessfully Cancelled As Per As Your Request..!</i>",
                parse_mode=enums.ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "Close", callback_data="cancel")
                        ]
                    ]
                )
            )
            await self._client.stop_transmission()

        if round(diff % float(5)) == 0 or current == total:
            try:
                percentage = current * 100 / total
                speed = current / diff
                elapsed_time = round(diff)
                time_to_completion = round((total - current) / speed)
                estimated_total_time = time_to_completion

                elapsed_time = TimeFormatter(seconds=elapsed_time)
                estimated_total_time = TimeFormatter(
                    seconds=estimated_total_time)

                progress = "[{0}{1}] \nP: {2}%\n".format(
                    "".join(["▣" for i in range(math.floor(percentage / 5))]),
                    "".join(
                        ["▢" for i in range(20 - math.floor(percentage / 5))]),
                    round(percentage, 2),
                )

                tmp = progress + "{0} of {1}\nSpeed: {2}/s\nETA: {3}\n".format(
                    humanbytes(current),
                    humanbytes(total),
                    humanbytes(speed),
                    # elapsed_time if elapsed_time != '' else "0 s",
                    estimated_total_time if estimated_total_time != "" else "0 s",
                )

                if not self._drive:
                    reply_markup = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "Cancel 🚫",
                                    callback_data=(
                                        f"cancel/{chat_id}/{mes_id}/{from_user}"
                                    ).encode("UTF-8"),
                                )
                            ]
                        ]
                    )
                else:
                    reply_markup = None
                try:
                    await self._mess.edit_text(
                        text="{}\n {}".format(ud_type, tmp),
                        reply_markup=reply_markup
                    )
                except FloodWait as fd:
                    logger.warning(f"{fd}")
                    await asyncio.sleep(fd.x)
                except Exception as e:
                    logger.info(e)

            except Exception:
                try:
                    if not self._drive:
                        reply_markup = InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "Cancel 🚫",
                                        callback_data=(
                                            f"cancel/{chat_id}/{mes_id}/{from_user}"
                                        ).encode("UTF-8"),
                                    )
                                ]
                            ]
                        )
                    else:
                        reply_markup = None
                    msg = ud_type.split(" ")[0]
                    await self._mess.edit_text(
                        text=f"<i>{msg} Your File....Please Be Patient...</i>",
                        parse_mode=enums.ParseMode.HTML,
                        reply_markup=reply_markup
                    )
                except:
                    pass




def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2 ** 10
    n = 0
    Dic_powerN = {0: " ", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + "B"


def TimeFormatter(seconds: int) -> str:
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + "d, ") if days else "")
        + ((str(hours) + "h, ") if hours else "")
        + ((str(minutes) + "m, ") if minutes else "")
        + ((str(seconds) + "s, ") if seconds else "")
    )
    return tmp[:-2]

