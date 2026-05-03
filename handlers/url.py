import re
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app

URL_REGEX  = re.compile(r"https?://\S+")
MAGNET_RE  = re.compile(r"magnet:\?xt=urn:btih:[a-zA-Z0-9]+")
GDRIVE_RE  = re.compile(r"https://drive\.google\.com/\S+")
MEGA_RE    = re.compile(r"https://mega\.nz/\S+")
YT_RE      = re.compile(r"https?://(www\.)?(youtube\.com|youtu\.be)/\S+")


def url_menu_kb(url: str, url_type: str) -> InlineKeyboardMarkup:
    enc = url[:200]   # truncate for callback_data safety
    rows = [
        [InlineKeyboardButton("📥 Mirror (as File)",  callback_data=f"dl_mirror|{enc}")],
        [InlineKeyboardButton("📥 Leech (as Media)",  callback_data=f"dl_leech|{enc}")],
    ]
    if url_type == "youtube":
        rows.insert(0, [InlineKeyboardButton("▶️ YouTube Download", callback_data=f"dl_ytdl|{enc}")])
    if url_type == "gdrive":
        rows.insert(0, [InlineKeyboardButton("📁 GDrive Download",  callback_data=f"dl_gdrive|{enc}")])
    if url_type == "mega":
        rows.insert(0, [InlineKeyboardButton("☁️ Mega Download",    callback_data=f"dl_mega|{enc}")])
    if url_type == "magnet":
        rows = [[InlineKeyboardButton("🧲 Torrent / Magnet",        callback_data=f"dl_torrent|{enc}")]]
    rows += [
        [InlineKeyboardButton("🔗 URL Uploader (Link→File)", callback_data=f"dl_urlup|{enc}")],
        [InlineKeyboardButton("📦 Extract Archive via Link", callback_data=f"dl_extractlink|{enc}")],
        [InlineKeyboardButton("✂️ Shorten URL",             callback_data=f"dl_shorten|{enc}"),
         InlineKeyboardButton("🔍 Unshorten URL",           callback_data=f"dl_unshorten|{enc}")],
        [InlineKeyboardButton("❌ Cancel",                  callback_data="cancel_menu")],
    ]
    return InlineKeyboardMarkup(rows)


@app.on_message(
    (filters.regex(URL_REGEX) | filters.regex(MAGNET_RE))
    & filters.private
    & ~filters.command([
        "start", "help", "about", "info", "stats", "broadcast",
        "ban", "unban", "settings", "cancel", "mirror", "leech",
        "status", "session", "m", "l", "ytdl", "torrent", "gdl",
        "mega", "nzb", "jd", "tgleech", "bulk_url", "upload",
        "gdrive", "rclone", "gofile", "pixeldrain", "buzzheavier", "ytvideo",
        "cancelall",
    ]),
    group=1,
)
async def url_handler(client: Client, message: Message):
    text = message.text or message.caption or ""

    magnet = MAGNET_RE.search(text)
    if magnet:
        url      = magnet.group()
        url_type = "magnet"
    else:
        url_match = URL_REGEX.search(text)
        if not url_match:
            return
        url = url_match.group()
        if YT_RE.match(url):
            url_type = "youtube"
        elif GDRIVE_RE.match(url):
            url_type = "gdrive"
        elif MEGA_RE.match(url):
            url_type = "mega"
        else:
            url_type = "direct"

    await message.reply_text(
        f"🔗 <b>Link detected</b>\n\n<code>{url[:100]}</code>\n\n"
        "Choose an action:",
        reply_markup=url_menu_kb(url, url_type),
        reply_to_message_id=message.id,
    )


URL_ACTIONS = {
    "dl_mirror":      "📥 Starting mirror task...",
    "dl_leech":       "📥 Starting leech task...",
    "dl_ytdl":        "▶️ Fetching YouTube info...",
    "dl_gdrive":      "📁 Connecting to Google Drive...",
    "dl_mega":        "☁️ Connecting to Mega.nz...",
    "dl_torrent":     "🧲 Adding torrent/magnet to queue...",
    "dl_urlup":       "🔗 Uploading link as file...",
    "dl_extractlink": "📦 Extracting archive from link...",
    "dl_shorten":     "✂️ Shortening URL...",
    "dl_unshorten":   "🔍 Unshortening URL...",
}


@app.on_callback_query(filters.regex(r"^(dl_[a-z_]+)\|(.+)$"))
async def url_action_cb(client: Client, cb: CallbackQuery):
    action, url = cb.data.split("|", 1)
    msg = URL_ACTIONS.get(action, "Processing...")
    await cb.answer()
    await cb.message.reply_text(
        f"{msg}\n\n🔗 <code>{url[:100]}</code>",
        reply_to_message_id=cb.message.id,
    )


# ── /bulk_url ─────────────────────────────────────────────────────────────────
@app.on_message(filters.command("bulk_url"))
async def bulk_url_cmd(client: Client, message: Message):
    await message.reply_text(
        "📋 <b>Bulk URL Downloader</b>\n\n"
        "Send multiple links (one per line). "
        "Optionally add a custom name after each link:\n\n"
        "<code>https://example.com/file1.zip MyFile1\n"
        "https://example.com/file2.zip MyFile2</code>",
        reply_to_message_id=message.id,
    )
