import asyncio
import psutil
import humanize
from pyrogram import Client, filters
from pyrogram.types import Message
from bot.client import app, get_uptime
from bot.database import db
from bot.script import Script
from config import Config


def admin_only(func):
    async def wrapper(client: Client, message: Message):
        if not Config.is_admin(message.from_user.id):
            await message.reply_text("❌ Admin only command.", reply_to_message_id=message.id)
            return
        return await func(client, message)
    wrapper.__name__ = func.__name__
    return wrapper


# ── /stats ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("stats"))
@admin_only
async def stats_cmd(client: Client, message: Message):
    global_stats = await db.get_global_stats()
    total_users  = await db.total_users()
    today_users  = await db.users_today()

    total_dl     = global_stats.get("total_downloads", 0)
    total_bytes  = global_stats.get("total_uploaded_bytes", 0)
    total_size   = humanize.naturalsize(total_bytes, binary=True)

    cpu  = psutil.cpu_percent(interval=0.5)
    ram  = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent

    text = Script.STATS_TXT.format(
        total_users=total_users,
        today_users=today_users,
        active_dl=0,          # plug into active task tracker if desired
        total_dl=total_dl,
        total_size=total_size,
        cpu=cpu,
        ram=ram,
        disk=disk,
        uptime=get_uptime(),
    )
    await message.reply_text(text, reply_to_message_id=message.id)


# ── /broadcast ────────────────────────────────────────────────────────────────
@app.on_message(filters.command("broadcast"))
@admin_only
async def broadcast_cmd(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text(
            "❗ Reply to a message to broadcast it.",
            reply_to_message_id=message.id
        )
        return

    broadcast_msg = message.reply_to_message
    user_ids      = await db.all_user_ids()
    sent, fail    = 0, 0

    status_msg = await message.reply_text(
        f"📢 Broadcasting to {len(user_ids)} users...",
        reply_to_message_id=message.id
    )

    for uid in user_ids:
        try:
            await broadcast_msg.copy(uid)
            sent += 1
            await asyncio.sleep(0.05)   # rate limit safety
        except Exception:
            fail += 1

    await status_msg.edit_text(
        f"✅ Broadcast complete!\n\n"
        f"👥 Total: {len(user_ids)}\n"
        f"✅ Sent: {sent}\n"
        f"❌ Failed: {fail}"
    )


# ── /ban ──────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("ban"))
@admin_only
async def ban_cmd(client: Client, message: Message):
    target_id = _get_target_id(message)
    if not target_id:
        await message.reply_text("Usage: /ban <user_id> or reply to user", reply_to_message_id=message.id)
        return
    await db.ban_user(target_id)
    await message.reply_text(f"🚫 User `{target_id}` banned.", reply_to_message_id=message.id)


# ── /unban ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("unban"))
@admin_only
async def unban_cmd(client: Client, message: Message):
    target_id = _get_target_id(message)
    if not target_id:
        await message.reply_text("Usage: /unban <user_id> or reply to user", reply_to_message_id=message.id)
        return
    await db.unban_user(target_id)
    await message.reply_text(f"✅ User `{target_id}` unbanned.", reply_to_message_id=message.id)


def _get_target_id(message: Message):
    if message.reply_to_message:
        return message.reply_to_message.from_user.id
    if len(message.command) > 1 and message.command[1].isdigit():
        return int(message.command[1])
    return None
