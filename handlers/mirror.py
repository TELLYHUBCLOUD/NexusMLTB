"""
Mirror, Leech, and download commands.
Actual download logic hooks into aria2c / yt-dlp / qbittorrent.
This file sets up command handlers and task queuing.
"""
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app, is_subscribed, fsub_keyboard
from bot.database import db
from config import Config

# Active tasks per user (simple in-memory queue; replace with Redis for scaling)
_active_tasks: dict[int, dict] = {}


def _cancel_kb(task_id: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_task|{task_id}")]
    ])


async def _require_sub(client, message):
    if not await is_subscribed(client, message.from_user.id):
        await message.reply_photo(
            photo=Config.MASSAGE_IMG_URL,
            caption="⚠️ Join our channels first!",
            reply_markup=fsub_keyboard(),
        )
        return False
    return True


# ── /mirror ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command(["mirror", "m"]))
async def mirror_cmd(client: Client, message: Message):
    if not await _require_sub(client, message):
        return

    link = " ".join(message.command[1:]).strip()
    if not link and message.reply_to_message:
        link = (message.reply_to_message.text or "").strip()

    if not link:
        await message.reply_text(
            "❌ Send a link after the command.\nUsage: <code>/mirror https://link</code>",
            reply_to_message_id=message.id,
        )
        return

    status_msg = await message.reply_text(
        f"📥 <b>Mirror task queued</b>\n\n🔗 <code>{link[:100]}</code>\n\n"
        "⏳ Connecting to aria2c...",
        reply_to_message_id=message.id,
        reply_markup=_cancel_kb(str(message.from_user.id)),
    )
    # TODO: plug aria2c / yt-dlp download here and update status_msg


# ── /leech ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command(["leech", "l"]))
async def leech_cmd(client: Client, message: Message):
    if not await _require_sub(client, message):
        return

    link = " ".join(message.command[1:]).strip()
    if not link and message.reply_to_message:
        link = (message.reply_to_message.text or "").strip()

    if not link:
        await message.reply_text(
            "❌ Usage: <code>/leech https://link</code>",
            reply_to_message_id=message.id,
        )
        return

    status_msg = await message.reply_text(
        f"📥 <b>Leech task queued</b>\n\n🔗 <code>{link[:100]}</code>\n\n"
        "⏳ Starting download...",
        reply_to_message_id=message.id,
        reply_markup=_cancel_kb(str(message.from_user.id)),
    )


# ── /ytdl ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("ytdl"))
async def ytdl_cmd(client: Client, message: Message):
    if not await _require_sub(client, message):
        return

    link = " ".join(message.command[1:]).strip()
    if not link:
        await message.reply_text("❌ Usage: <code>/ytdl https://youtube.com/...</code>",
                                 reply_to_message_id=message.id)
        return

    await message.reply_text(
        f"▶️ <b>YouTube Download queued</b>\n\n🔗 <code>{link[:100]}</code>\n\n"
        "⏳ Fetching video info via yt-dlp...",
        reply_to_message_id=message.id,
        reply_markup=_cancel_kb(str(message.from_user.id)),
    )


# ── /torrent ──────────────────────────────────────────────────────────────────
@app.on_message(filters.command("torrent"))
async def torrent_cmd(client: Client, message: Message):
    if not await _require_sub(client, message):
        return

    link = " ".join(message.command[1:]).strip()
    if not link:
        await message.reply_text(
            "❌ Usage: <code>/torrent magnet:?xt=...</code> or send a .torrent file.",
            reply_to_message_id=message.id
        )
        return

    await message.reply_text(
        f"🧲 <b>Torrent queued</b>\n\n<code>{link[:100]}</code>\n\n"
        "⏳ Adding to qBittorrent/aria2c...",
        reply_to_message_id=message.id,
        reply_markup=_cancel_kb(str(message.from_user.id)),
    )


# ── /status ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("status"))
async def status_cmd(client: Client, message: Message):
    uid   = message.from_user.id
    tasks = _active_tasks.get(uid)
    if not tasks:
        await message.reply_text("ℹ️ No active downloads.", reply_to_message_id=message.id)
        return
    await message.reply_text(f"📊 Active tasks:\n{tasks}", reply_to_message_id=message.id)


# ── /cancel ───────────────────────────────────────────────────────────────────
@app.on_message(filters.command("cancel"))
async def cancel_cmd(client: Client, message: Message):
    uid = message.from_user.id
    if uid in _active_tasks:
        _active_tasks.pop(uid, None)
        await message.reply_text("❌ Task cancelled.", reply_to_message_id=message.id)
    else:
        await message.reply_text("ℹ️ No active task.", reply_to_message_id=message.id)


@app.on_callback_query(filters.regex(r"^cancel_task\|(.+)$"))
async def cancel_task_cb(client: Client, cb):
    task_uid = cb.data.split("|", 1)[1]
    _active_tasks.pop(int(task_uid), None)
    await cb.answer("✅ Cancelled!")
    await cb.message.edit_text("❌ Task cancelled by user.")
