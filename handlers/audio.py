from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app

AUDIO_MIME = {"audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav",
              "audio/flac", "audio/aac", "audio/x-wav", "audio/opus"}


def audio_menu_kb(file_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Caption & Buttons Editor",   callback_data=f"aud_caption|{file_id}")],
        [InlineKeyboardButton("2️⃣ Slowed & Reverb Maker",      callback_data=f"aud_slowreverb|{file_id}")],
        [InlineKeyboardButton("3️⃣ Audio Converter",            callback_data=f"aud_convert|{file_id}")],
        [InlineKeyboardButton("4️⃣ Make Archive",               callback_data=f"aud_archive|{file_id}")],
        [InlineKeyboardButton("5️⃣ Audio Merger",               callback_data=f"aud_merge|{file_id}")],
        [InlineKeyboardButton("6️⃣ 8D Audio Converter",         callback_data=f"aud_8d|{file_id}")],
        [InlineKeyboardButton("7️⃣ Music Equalizer",            callback_data=f"aud_eq|{file_id}")],
        [InlineKeyboardButton("8️⃣ Bass Booster",               callback_data=f"aud_bass|{file_id}"),
         InlineKeyboardButton("9️⃣ Treble Booster",             callback_data=f"aud_treble|{file_id}")],
        [InlineKeyboardButton("🔟 Audio Trimmer",              callback_data=f"aud_trim|{file_id}")],
        [InlineKeyboardButton("⏱ Auto Trimmer",               callback_data=f"aud_autotrim|{file_id}")],
        [InlineKeyboardButton("✏️ Rename Audio",               callback_data=f"aud_rename|{file_id}")],
        [InlineKeyboardButton("🏷 Audio Tag Editor",           callback_data=f"aud_tag|{file_id}")],
        [InlineKeyboardButton("⚡ Speed Changer",              callback_data=f"aud_speed|{file_id}")],
        [InlineKeyboardButton("🔊 Volume Changer",             callback_data=f"aud_volume|{file_id}")],
        [InlineKeyboardButton("ℹ️ Media Info",                 callback_data=f"aud_mediainfo|{file_id}")],
        [InlineKeyboardButton("🗜 Compress Audio",             callback_data=f"aud_compress|{file_id}")],
        [InlineKeyboardButton("❌ Cancel",                     callback_data="cancel_menu")],
    ])


@app.on_message(filters.audio)
async def audio_handler(client: Client, message: Message):
    audio = message.audio
    if not audio:
        return

    file_id = audio.file_id
    name    = audio.file_name or audio.title or "audio"

    await message.reply_text(
        f"🎵 <b>Audio detected:</b> <code>{name}</code>\n\n"
        "Choose what you want to do with this audio:",
        reply_markup=audio_menu_kb(file_id),
        reply_to_message_id=message.id,
    )


AUDIO_CALLBACKS = {
    "aud_caption":    "✏️ Reply with new caption and buttons.",
    "aud_slowreverb": "🌊 Creating slowed + reverb version...",
    "aud_convert":    "🔄 Send target format: mp3 / wav / flac / aac / opus / ogg",
    "aud_archive":    "📦 Choose: ZIP / RAR / 7Z (reply with type and optional password)",
    "aud_merge":      "🔗 Send another audio file to merge.",
    "aud_8d":         "🎧 Converting to 8D audio...",
    "aud_eq":         "🎚 Send EQ values: Volume Bass Treble Speed",
    "aud_bass":       "🎸 Send bass boost range (-20 to 20):",
    "aud_treble":     "🎶 Send treble boost range (-20 to 20):",
    "aud_trim":       "✂️ Send trim range: <code>00:00:30 - 00:01:30</code>",
    "aud_autotrim":   "⏱ Send start time and duration: <code>00:00:10 30</code>",
    "aud_rename":     "✏️ Send new filename (without extension):",
    "aud_tag":        "🏷 Send Album Art image to update tags.",
    "aud_speed":      "⚡ Send speed % (50-200):",
    "aud_volume":     "🔊 Send volume % (10-200):",
    "aud_mediainfo":  "ℹ️ Fetching media info...",
    "aud_compress":   "🗜 Compressing audio...",
}


@app.on_callback_query(filters.regex(r"^(aud_[a-z_]+)\|(.+)$"))
async def audio_action_cb(client: Client, cb: CallbackQuery):
    action, file_id = cb.data.split("|", 1)
    msg = AUDIO_CALLBACKS.get(action, "Processing...")
    await cb.answer()
    await cb.message.reply_text(
        f"{msg}\n\n<i>⚙️ Powered by FFmpeg audio engine.</i>",
        reply_to_message_id=cb.message.id,
    )
