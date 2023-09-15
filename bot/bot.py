

import time
import string
import random
import asyncio

from collections import defaultdict
from contextlib import contextmanager

from pyrogram import Client, enums, __version__
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import LOGGER, Config
from bot.plugins.admin.broadcast import Broadcast
from pyropatch import listen

class Bot(Client):

    def __init__(self):
        super().__init__(
            "bot",
            api_id=Config.APP_ID,
            api_hash=Config.API_HASH,
            plugins={
                "root": "bot/plugins"
            },
            workers=400,
            bot_token=Config.BOT_TOKEN
        )
        self.LOGGER = LOGGER
        self.CHAT_DELAY = defaultdict(lambda: int(time.time()) - Config.REQUEST_DELAY - 1)
        self.broadcast_ids = {}

    async def start(self):
        await super().start()
        usr_bot_me = await self.get_me()
        self.set_parse_mode(enums.ParseMode.HTML)
        self.LOGGER(__name__).info(
            f"@{usr_bot_me.username}  started! "
        )

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped. Bye.")

    @contextmanager
    def track_broadcast(self, handler):
        broadcast_id = ""
        while True:
            broadcast_id = "".join(
                random.choice(string.ascii_letters) for _ in range(3)
            )
            if broadcast_id not in self.broadcast_ids:
                break

        self.broadcast_ids[broadcast_id] = handler
        try:
            yield broadcast_id
        finally:
            self.broadcast_ids.pop(broadcast_id)

    async def start_broadcast(self, broadcast_message, message, admin_id):
        asyncio.create_task(self._start_broadcast(broadcast_message, message, admin_id))

    async def _start_broadcast(self, broadcast_message, message, admin_id):
        try:
            broadcast_handler = Broadcast(
                client=self, message=message, broadcast_message=broadcast_message, 
            )
            with self.track_broadcast(broadcast_handler) as broadcast_id:
                reply_message = await self.send_message(
                    chat_id=admin_id,
                    text="Broadcast started. Use the buttons to check the progress or to cancel the broadcast.",
                    reply_to_message_id=broadcast_message.id,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    text="Check Progress",
                                    callback_data=f"sts_bdct+{broadcast_id}",
                                ),
                                InlineKeyboardButton(
                                    text="Cancel!",
                                    callback_data=f"cncl_bdct+{broadcast_id}",
                                ),
                            ]
                        ]
                    ),
                )

                await broadcast_handler.start()

                await reply_message.edit_text("Broadcast completed")
        except Exception as e:
            self.LOGGER.error(e, exc_info=True)


