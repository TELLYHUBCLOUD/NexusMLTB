from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app

ARCHIVE_EXTS = {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"}
SUBTITLE_EXTS = {".srt", ".vtt", ".ass", ".sbv", ".sub"}
JSON_EXTS = {".json"}


def doc_menu_kb(file_id: str, doc_type: str) -> InlineKeyboardMarkup:
    base = [
        [InlineKeyboardButton("1️⃣ File Renamer",           callback_data=f"doc_rename|{file_id}")],
        [InlineKeyboardButton("2️⃣ Create Archive (ZIP)",   callback_data=f"doc_archive|{file_id}")],
        [InlineKeyboardButton("3️⃣ Archive Extractor",      callback_data=f"doc_extract|{file_id}")],
        [InlineKeyboardButton("4️⃣ Caption & Buttons",      callback_data=f"doc_caption|{file_id}")],
        [InlineKeyboardButton("5️⃣ Forward Tag Remover",    callback_data=f"doc_fwdremove|{file_id}")],
    ]
    if doc_type == "subtitle":
        base.append([InlineKeyboardButton("6️⃣ Subtitle Converter", callback_data=f"doc_subconvert|{file_id}")])
    if doc_type == "json":
        base.append([InlineKeyboardButton("7️⃣ JSON Formatter",     callback_data=f"doc_jsonformat|{file_id}")])
    base.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_menu")])
    return InlineKeyboardMarkup(base)


@app.on_message(filters.document & ~filters.audio & ~filters.video)
async def doc_handler(client: Client, message: Message):
    doc  = message.document
    name = (doc.file_name or "").lower()

    # Let video handler take video documents
    if any(name.endswith(ext) for ext in [".mp4", ".mkv", ".avi", ".webm", ".mov", ".m4v"]):
        return

    doc_type = "generic"
    if any(name.endswith(ext) for ext in SUBTITLE_EXTS):
        doc_type = "subtitle"
    elif any(name.endswith(ext) for ext in JSON_EXTS):
        doc_type = "json"

    await message.reply_text(
        f"📄 <b>Document detected:</b> <code>{doc.file_name or 'file'}</code>\n\n"
        "Choose what you want to do:",
        reply_markup=doc_menu_kb(doc.file_id, doc_type),
        reply_to_message_id=message.id,
    )


DOC_CALLBACKS = {
    "doc_rename":     "✏️ Send the new filename (with extension):",
    "doc_archive":    "📦 Send archive type and optional password:\n<code>zip [password]</code>",
    "doc_extract":    "📂 Extracting archive...",
    "doc_caption":    "✏️ Reply with new caption.",
    "doc_fwdremove":  "🔄 Removing forward tag and re-uploading...",
    "doc_subconvert": "🔄 Send target format: srt / vtt / ass / sbv",
    "doc_jsonformat": "📋 Send indent level (1-4):",
}


@app.on_callback_query(filters.regex(r"^(doc_[a-z_]+)\|(.+)$"))
async def doc_action_cb(client: Client, cb: CallbackQuery):
    action, file_id = cb.data.split("|", 1)
    msg = DOC_CALLBACKS.get(action, "Processing...")
    await cb.answer()
    await cb.message.reply_text(msg, reply_to_message_id=cb.message.id)
