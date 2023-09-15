
# import os
# from pyrogram.types.messages_and_media.message import Message
# from pyrogram import filters, Client, enums
# from bot.plugins import Config, LOGGER  # pylint: disable=import-error
# from bot.database.database import Database  

# logger = LOGGER(__name__)
# db = Database()


# @Client.on_message(filters.photo & filters.user(Config.AUTH_USERS))
# async def save_thumb(bot, update):

#     user_id = update.from_user.id

#     sent_message = await bot.send_message(
#         chat_id=update.chat.id,
#         text="`Saving Your Thumbanil....⌛`",
#         reply_to_message_id=update.message_id,
#         parse_mode=enums.ParseMode.MARKDOWN
#     )

#     if update.media_group_id is not None:
#         file_id = update[0].photo.file_id
#         await db.add_thumb(user_id, file_id)
#     else:
#         file_id = update.photo.file_id
#         await db.add_thumb(user_id, file_id)

#     download_location = "/app/downloads/" + str(user_id) + "/thumbnail.jpg"

#     await bot.download_media(
#         message=update,
#         file_name=download_location
#     )

#     await sent_message.edit_text(
#         text="Sucessfully Saved Your Thumbnail..",
#     )


# @Client.on_message(filters.command(["delthumb"]) & filters.user(Config.AUTH_USERS))
# async def delete_thumbnail(bot, update):

#     sent_message = await bot.send_message(
#         chat_id=update.chat.id,
#         text="`Deleting Your Thumbanil.....⌛`",
#         reply_to_message_id=update.id,
#         parse_mode=enums.ParseMode.MARKDOWN
#     )

#     download_location = "/app/downloads/" + str(update.from_user.id) + "/thumbnail.jpg"

#     try:
#         await db.del_thumb(update.from_user.id)
#         os.remove(download_location)
#     except:
#         pass

#     await sent_message.edit_text(
#         text="Sucessfully Deleted Your Thumbnail.."
#     )


# @Client.on_message(filters.regex("^/showthumb") & filters.user(Config.AUTH_USERS))
# async def show_thumbnail(bot: Client, update: Message):

#     sent_message = await bot.send_message(
#         chat_id=update.chat.id,
#         text="`Processing.....⌛`",
#         parse_mode=enums.ParseMode.MARKDOWN

#     )

#     download_location = "/app/downloads/" + str(update.from_user.id) + "/thumbnail.jpg"
#     fid = await db.get_thumb(update.from_user.id)
#     logger.info(fid)
#     if fid != None:

#         await bot.download_media(fid, file_name=download_location)
#         await sent_message.delete()
#         await bot.send_photo(
#             chat_id=update.chat.id,
#             photo=fid,
#             caption="Your Saved Thumbnail.."
#         )

#     else:
#         await sent_message.edit_text(
#             text="You Dont Have Any Saved Thumbnail..."
#         )

