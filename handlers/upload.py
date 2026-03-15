from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app


def _upload_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📁 Google Drive",  callback_data="up_gdrive"),
         InlineKeyboardButton("☁️ RClone",        callback_data="up_rclone")],
        [InlineKeyboardButton("📂 GoFile",        callback_data="up_gofile"),
         InlineKeyboardButton("📤 PixelDrain",    callback_data="up_pixeldrain")],
        [InlineKeyboardButton("📦 BuzzHeavier",   callback_data="up_buzzheavier"),
         InlineKeyboardButton("▶️ YouTube",       callback_data="up_youtube")],
        [InlineKeyboardButton("❌ Cancel",         callback_data="cancel_menu")],
    ])


@app.on_message(filters.command("upload"))
async def upload_cmd(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(
            "❗ Reply to a file to upload it somewhere.",
            reply_to_message_id=message.id,
        )
        return
    await message.reply_text(
        "☁️ <b>Choose upload destination:</b>",
        reply_markup=_upload_menu(),
        reply_to_message_id=message.id,
    )


UPLOAD_ACTIONS = {
    "up_gdrive":      "📁 Uploading to Google Drive...",
    "up_rclone":      "☁️ Uploading via RClone...",
    "up_gofile":      "📂 Uploading to GoFile.io...",
    "up_pixeldrain":  "📤 Uploading to PixelDrain...",
    "up_buzzheavier": "📦 Uploading to BuzzHeavier...",
    "up_youtube":     "▶️ Uploading to YouTube...",
}


@app.on_callback_query(filters.regex(r"^up_[a-z]+$"))
async def upload_cb(client: Client, cb):
    msg = UPLOAD_ACTIONS.get(cb.data, "Uploading...")
    await cb.answer()
    await cb.message.reply_text(msg, reply_to_message_id=cb.message.id)


# ── Specific upload commands ──────────────────────────────────────────────────
for _cmd, _label in [
    ("gdrive",      "📁 Google Drive"),
    ("rclone",      "☁️ RClone"),
    ("gofile",      "📂 GoFile.io"),
    ("pixeldrain",  "📤 PixelDrain"),
    ("buzzheavier", "📦 BuzzHeavier"),
    ("ytvideo",     "▶️ YouTube"),
]:
    @app.on_message(filters.command(_cmd))
    async def _up_cmd(client: Client, message: Message, label=_label):
        if not message.reply_to_message:
            await message.reply_text(
                f"❗ Reply to a file to upload to {label}.",
                reply_to_message_id=message.id,
            )
            return
        await message.reply_text(
            f"{label} upload starting...",
            reply_to_message_id=message.id,
        )
