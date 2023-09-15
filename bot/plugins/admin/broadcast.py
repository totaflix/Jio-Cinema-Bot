

import traceback
import datetime
import logging
import asyncio
import time
import io

from pyrogram import Client, filters, enums
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    UserIsBlocked,
    PeerIdInvalid,
)

from . import User as db, Config

log = logging.getLogger(__name__)


class Broadcast:
    def __init__(self, client, message, broadcast_message):
        self.client = client
        self.message = message
        self.broadcast_message = broadcast_message

        self.cancelled = False
        self.progress = dict(total=0, current=0, failed=0, success=0)

    def get_progress(self):
        return self.progress

    def cancel(self):
        self.cancelled = True

    async def _send_msg(self, user_id):
        try:
            await self.broadcast_message.copy(chat_id=user_id)
            return 200, None
        except FloodWait as e:
            await asyncio.sleep(e.value + 1)
            return self._send_msg(user_id)
        except InputUserDeactivated as e:
            log.error(e)
            return 400, f"{user_id} : deactivated\n"
        except UserIsBlocked as e:
            log.error(e)
            return 310, f"{user_id} : blocked the bot\n"
        except PeerIdInvalid as e:
            log.error(e)
            return 400, f"{user_id} : user id invalid\n"
        except Exception as e:
            log.error(e, exc_info=True)
            return 500, f"{user_id} : {traceback.format_exc()}\n"

    async def start(self):
        
        all_users = await db().get_all_users()
        start_time = time.time()
        total_users = await db().get_all_users_count()
        done = 0
        failed = 0
        success = 0

        log_file = io.BytesIO()
        log_file.name = f"{datetime.datetime.utcnow()}_broadcast.txt"
        broadcast_log = ""
        for user in all_users:
          
            await asyncio.sleep(0.5)
            sts, msg = await self._send_msg(user_id=int(user["_id"]))
            if msg is not None:
                broadcast_log += msg

            if sts == 200:
                success += 1
            else:
                failed += 1

            if sts == 310:
                prev = await db().get_user(int(user["_id"]))
                join_date = prev["status"]["joined_date"]
                last_date = prev["status"]["last_used_on"]
                await db().update_status(int(user["_id"]), {'active': False, "joined_date": join_date, "last_used_on": last_date})
                prev = join_date = last_date = None
            elif sts > 310:
                await db().remove_user(int(user["_id"]))

            done += 1
            self.progress.update(dict(current=done, failed=failed, success=success))
            if self.cancelled:
                break

        log_file.write(broadcast_log.encode())
        completed_in = datetime.timedelta(seconds=int(time.time() - start_time))
        await asyncio.sleep(3)
        update_text = (
            f"#broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\n"
            f"Total done {done}, {success} success and {failed} failed.\n"
            "Status: {}".format("Completed" if not self.cancelled else "Cancelled")
        )

        if failed == 0:
            await self.client.send_message(
                chat_id=self.message.chat.id,
                text=update_text,
            )
        else:
            await self.client.send_document(
                chat_id=self.message.chat.id,
                document=log_file,
                caption=update_text,
            )



@Client.on_message(filters.command(["totalusers"]) & filters.user(Config.AUTH_USERS), -1)
async def broadcastable_user_count(bot, update):
    
    count = await db().get_all_users_count()
    
    await update.reply_text(
        f"<i>Total Users: <code>{count}</code></i>",
        True,
        parse_mode=enums.ParseMode.HTML
    )
    

@Client.on_message(filters.command(["broadcast"]) & filters.user(Config.AUTH_USERS), -1)
async def boradcast(bot, update):
    
    if not update.reply_to_message:
        await update.reply_text(
            "<b><i>Please Reply To A Message To Brodacst...!</i></b>",
            True,
            parse_mode=enums.ParseMode.HTML
        )
    
    else:
        await bot.start_broadcast(
            broadcast_message=update.reply_to_message, message=update, admin_id=update.from_user.id
        )
        



@Client.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("sts_bdct")) & filters.user(Config.AUTH_USERS), 2)
async def sts_broadcast_(bot, update):

    _, broadcast_id = update.data.split("+")

    if not bot.broadcast_ids.get(broadcast_id):
        await update.answer(
            text=f"No active broadcast with id {broadcast_id}", show_alert=True
        )
        return

    sts_txt = ""
    broadcast_handler = bot.broadcast_ids[broadcast_id]
    broadcast_progress = broadcast_handler.get_progress()
    for key, value in broadcast_progress.items():
        sts_txt += f"{key} = {value}\n"

    await update.answer(
        text=f"Broadcast Status for {broadcast_id}\n\n{sts_txt}", show_alert=True
    )



@Client.on_callback_query(filters.create(lambda _, __, query: query.data.startswith("cncl_bdct")) & filters.user(Config.AUTH_USERS), 2)
async def cncl_broadcast_(bot, update):

    _, broadcast_id = update.data.split("+")

    if not bot.broadcast_ids.get(broadcast_id):
        await update.answer(
            text=f"No active broadcast with id {broadcast_id}", show_alert=True
        )
        return

    broadcast_handler = bot.broadcast_ids[broadcast_id]
    broadcast_handler.cancel()

    await update.answer(text="Broadcast will be canceled soon.", show_alert=True)

    
