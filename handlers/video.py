from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app

VIDEO_MIME = {"video/mp4", "video/x-matroska", "video/avi", "video/webm",
              "video/x-msvideo", "video/quicktime", "video/3gpp"}


def video_menu_kb(file_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("1️⃣ Audio & Subs Remover",    callback_data=f"vid_rem_audsub|{file_id}")],
        [InlineKeyboardButton("2️⃣ Audio & Subs Extractor",  callback_data=f"vid_ext_audsub|{file_id}")],
        [InlineKeyboardButton("3️⃣ Caption & Buttons Editor",callback_data=f"vid_caption|{file_id}")],
        [InlineKeyboardButton("4️⃣ Video Trimmer",           callback_data=f"vid_trim|{file_id}")],
        [InlineKeyboardButton("5️⃣ Video Merger",            callback_data=f"vid_merge|{file_id}")],
        [InlineKeyboardButton("6️⃣ Mute Audio",              callback_data=f"vid_mute|{file_id}")],
        [InlineKeyboardButton("7️⃣ Video + Audio Merger",    callback_data=f"vid_aud_merge|{file_id}")],
        [InlineKeyboardButton("8️⃣ Video + Subtitle Merger", callback_data=f"vid_sub_merge|{file_id}")],
        [InlineKeyboardButton("9️⃣ Video → GIF",             callback_data=f"vid_gif|{file_id}")],
        [InlineKeyboardButton("🔟 Video Splitter",          callback_data=f"vid_split|{file_id}")],
        [InlineKeyboardButton("📸 Screenshot Generator",    callback_data=f"vid_screenshot|{file_id}"),
         InlineKeyboardButton("📸 Manual Screenshot",      callback_data=f"vid_screenshot_m|{file_id}")],
        [InlineKeyboardButton("🎬 Sample Generator",        callback_data=f"vid_sample|{file_id}")],
        [InlineKeyboardButton("🎵 Video → Audio Converter", callback_data=f"vid_to_audio|{file_id}")],
        [InlineKeyboardButton("⚡ Video Optimizer",         callback_data=f"vid_optimize|{file_id}")],
        [InlineKeyboardButton("🔄 Video Converter",         callback_data=f"vid_convert|{file_id}")],
        [InlineKeyboardButton("✏️ Video Renamer",           callback_data=f"vid_rename|{file_id}")],
        [InlineKeyboardButton("ℹ️ Media Info",              callback_data=f"vid_mediainfo|{file_id}")],
        [InlineKeyboardButton("📦 Make Archive",            callback_data=f"vid_archive|{file_id}")],
        [InlineKeyboardButton("❌ Cancel",                  callback_data="cancel_menu")],
    ])


@app.on_message(filters.video)
async def video_handler(client: Client, message: Message):
    media = message.video or message.document
    if not media:
        return

    mime = getattr(media, "mime_type", "") or ""
    name = getattr(media, "file_name", "") or ""

    is_video = (
        message.video is not None or
        mime in VIDEO_MIME or
        any(name.lower().endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".webm", ".mov", ".m4v"])
    )

    if not is_video:
        return  # Handled by document/audio handler

    file_id = media.file_id
    await message.reply_text(
        f"🎬 <b>Video detected:</b> <code>{name or 'video'}</code>\n\n"
        "Choose what you want to do with this video:",
        reply_markup=video_menu_kb(file_id),
        reply_to_message_id=message.id,
    )


# ── Stub callbacks — real ffmpeg logic plugs in here ─────────────────────────
VIDEO_CALLBACKS = {
    "vid_rem_audsub":   "🔇 Removing audio & subtitles...",
    "vid_ext_audsub":   "📤 Extracting audio & subtitles...",
    "vid_caption":      "✏️ Caption editor — reply with new caption.",
    "vid_trim":         "✂️ Send trim range: <code>00:01:00 - 00:02:30</code>",
    "vid_merge":        "🔗 Send another video to merge.",
    "vid_mute":         "🔇 Muting audio...",
    "vid_aud_merge":    "🎵 Send audio file to merge with video.",
    "vid_sub_merge":    "📄 Send subtitle file (.srt/.ass/.vtt) to embed.",
    "vid_gif":          "🎞 Converting to GIF... (first 10 seconds)",
    "vid_split":        "✂️ Send split duration in seconds: e.g. <code>300</code>",
    "vid_screenshot":   "📸 Generating screenshots...",
    "vid_screenshot_m": "📸 Send timestamp for screenshot: e.g. <code>00:01:30</code>",
    "vid_sample":       "🎬 Generating 30-second sample...",
    "vid_to_audio":     "🎵 Choose output format:",
    "vid_optimize":     "⚡ Optimizing video for web playback...",
    "vid_convert":      "🔄 Choose output format: MKV / MP4 / AVI / WebM",
    "vid_rename":       "✏️ Send new filename (without extension):",
    "vid_mediainfo":    "ℹ️ Fetching media info...",
    "vid_archive":      "📦 Choose archive type: ZIP / RAR / 7Z",
}


@app.on_callback_query(filters.regex(r"^(vid_[a-z_]+)\|(.+)$"))
async def video_action_cb(client: Client, cb: CallbackQuery):
    action, file_id = cb.data.split("|", 1)
    msg = VIDEO_CALLBACKS.get(action, "Processing...")
    await cb.answer()
    await cb.message.reply_text(
        f"{msg}\n\n<i>⚙️ Processing powered by FFmpeg engine.</i>",
        reply_to_message_id=cb.message.id,
    )


@app.on_callback_query(filters.regex("^cancel_menu$"))
async def cancel_menu(client: Client, cb: CallbackQuery):
    await cb.message.delete()
