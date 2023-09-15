
class Script(object):
    
    START_TEXT = """<b>Hi {}!!</b>
Welcome To <b>JioCinema Dl Bot</b>
<i>I can download Jio Cinema movies to telegram or cloud</i>
<b>Send me a Jio Cinema link to start</b>
/help for more info

<code>Note: You need to be a premium bot user to download movies. Buy Subscription from</code> @Calicum_R4SL <code>at ₹200/month</code>
"""

    HELP_TEXT = """<b><u>Help</u></b>

Just send me a Jio Cinema link to start.
Choose the quality you want to download.
Wait for the download to complete.
Enjoy your movie.

"""

    ABOUT_TEXT = """
✯ ᴄʀᴇᴀᴛᴏʀ: <a href="https://t.me/Calicum_R4SL">Calicum</a>
✯ ʟɪʙʀᴀʀʏ: ᴘʏʀᴏɢʀᴀᴍ
✯ ʟᴀɴɢᴜᴀɢᴇ: ᴘʏᴛʜᴏɴ
✯ ʙᴜɪʟᴅ ꜱᴛᴀᴛᴜꜱ: ᴠ2.0
"""

    MOVIE_NOT_FOUND = "No movie found with this URL. Please check the URL and try again."

    FORMATS_NOT_FOUND = 'No Formats Found..!'

    SELECT_FORMAT = "Select the format to download"

    OUTDATED_MSG = "This message is outdated. Please try again."

    DOWNLOADING_CONTENT = "Downloading your content...⏳"

    FAILED_TO_DOWNLOAD = "Failed to download your content...❌"

    FILE_SIZE_TOO_LARGE = "File size is too large to upload...❌\nUploading to drive..."

    SOMETHING_WRONG = "Something went wrong...❌"

    INDEX_LINK_MSG = "**{}**\n\n**Download Link:** `{}`" # Should be in Markdown


