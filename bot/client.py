import asyncio
import time
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from bot.database import db


# ── Pyrogram Client ────────────────────────────────────────────────────────────
app = Client(
    "MirrorNexusBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    workers=Config.WORKERS,
    sleep_threshold=60,
)

BOT_START_TIME = time.time()


# ── Force Subscribe Check ──────────────────────────────────────────────────────
async def is_subscribed(client: Client, user_id: int) -> bool:
    channels = [c for c in [Config.FSUB_CHANNEL_1, Config.FSUB_CHANNEL_2] if c]
    if not channels:
        return True  # No FSUB channels configured — allow everyone
    # Admins always pass
    if Config.is_admin(user_id):
        return True
    for channel in channels:
        try:
            member = await client.get_chat_member(channel, user_id)
            if member.status.value in ("left", "banned", "restricted"):
                return False
        except Exception as e:
            import logging
            logging.getLogger("MirrorNexus").warning(
                f"⚠️ FSUB check failed for channel={channel}, user={user_id}: {e} — allowing access"
            )
            # Don't block users when the bot can't verify (bot not admin, channel deleted, etc.)
            continue
    return True


# ── Force-Sub Inline Keyboard ──────────────────────────────────────────────────
def fsub_keyboard():
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    if Config.FSUB_CHANNEL_1:
        buttons.append([InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/zerodev2")])
    if Config.FSUB_CHANNEL_2:
        buttons.append([InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/mvxyoffcail")])
    buttons.append([InlineKeyboardButton("✅ Try Again", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)


# ── Fetch random welcome image ─────────────────────────────────────────────────
async def get_welcome_image_url() -> str:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(Config.WELCOME_IMG_API, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                if resp.status == 200:
                    # API returns an image directly — return the URL itself
                    return str(resp.url)
    except Exception:
        pass
    return Config.MASSAGE_IMG_URL


# ── Uptime helper ──────────────────────────────────────────────────────────────
def get_uptime() -> str:
    elapsed = int(time.time() - BOT_START_TIME)
    days    = elapsed // 86400
    hours   = (elapsed % 86400) // 3600
    mins    = (elapsed % 3600) // 60
    secs    = elapsed % 60
    return f"{days}d {hours}h {mins}m {secs}s"
