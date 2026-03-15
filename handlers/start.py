import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
)
from bot.client import app, is_subscribed, fsub_keyboard, get_welcome_image_url
from bot.database import db
from bot.script import Script
from config import Config


# ── /start ─────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user

    # Save user to DB
    await db.add_user(user.id, {
        "first_name": user.first_name or "",
        "username":   user.username or "",
    })

    # Force subscribe check
    if not await is_subscribed(client, user.id):
        await message.reply_photo(
            photo=Config.MASSAGE_IMG_URL,
            caption=Script.FORCE_SUB_TXT,
            reply_markup=fsub_keyboard(),
        )
        return

    # Send animated sticker (auto-delete after 2 seconds)
    sticker_msg = await message.reply_sticker(Config.STICKER_ID)
    await asyncio.sleep(2)
    await sticker_msg.delete()

    # Send welcome message with random image
    img_url = await get_welcome_image_url()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Commands", callback_data="help"),
            InlineKeyboardButton("ℹ️ About",    callback_data="about"),
        ],
        [
            InlineKeyboardButton("📢 Channel 1", url="https://t.me/zerodev2"),
            InlineKeyboardButton("📢 Channel 2", url="https://t.me/mvxyoffcail"),
        ],
        [
            InlineKeyboardButton("🔐 Session String", callback_data="session_info"),
        ],
    ])

    await message.reply_photo(
        photo=img_url,
        caption=Script.START_TXT.format(user.mention),
        reply_markup=keyboard,
    )


# ── /start in groups ───────────────────────────────────────────────────────────
@app.on_message(filters.command("start") & filters.group)
async def start_group(client: Client, message: Message):
    await message.reply_text(
        "<b>💎 Mirror Nexus is active here!\n\nUse /help to see all commands.</b>",
        reply_to_message_id=message.id,
    )


# ── Callback: check_sub ────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^check_sub$"))
async def check_sub_cb(client: Client, cb: CallbackQuery):
    if await is_subscribed(client, cb.from_user.id):
        await cb.message.delete()
        # Re-trigger start flow
        fake = cb.message
        fake.from_user = cb.from_user
        await start_handler(client, fake)
    else:
        await cb.answer("❌ You haven't joined yet!", show_alert=True)


# ── Callback: help ────────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^help$"))
async def help_cb(client: Client, cb: CallbackQuery):
    await cb.message.edit_caption(
        caption=Script.HELP_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]),
    )


# ── Callback: about ───────────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^about$"))
async def about_cb(client: Client, cb: CallbackQuery):
    await cb.message.edit_caption(
        caption=Script.ABOUT_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="start")]
        ]),
    )


# ── Callback: back to start ───────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^start$"))
async def back_start_cb(client: Client, cb: CallbackQuery):
    user = cb.from_user
    img_url = await get_welcome_image_url()
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Commands", callback_data="help"),
            InlineKeyboardButton("ℹ️ About",    callback_data="about"),
        ],
        [
            InlineKeyboardButton("📢 Channel 1", url="https://t.me/zerodev2"),
            InlineKeyboardButton("📢 Channel 2", url="https://t.me/mvxyoffcail"),
        ],
        [
            InlineKeyboardButton("🔐 Session String", callback_data="session_info"),
        ],
    ])
    try:
        await cb.message.edit_media(
            media=__import__("pyrogram.types", fromlist=["InputMediaPhoto"]).InputMediaPhoto(media=img_url)
        )
    except Exception:
        pass
    await cb.message.edit_caption(
        caption=Script.START_TXT.format(user.mention),
        reply_markup=keyboard,
    )


# ── Callback: session info ────────────────────────────────────────────────────
@app.on_callback_query(filters.regex("^session_info$"))
async def session_info_cb(client: Client, cb: CallbackQuery):
    await cb.answer(
        "Use /session command in private chat to generate your session string.",
        show_alert=True
    )


# ── /help ─────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("help"))
async def help_cmd(client: Client, message: Message):
    await message.reply_text(
        Script.HELP_TXT,
        reply_to_message_id=message.id,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel 1", url="https://t.me/zerodev2"),
             InlineKeyboardButton("📢 Join Channel 2", url="https://t.me/mvxyoffcail")],
        ]),
    )


# ── /about ────────────────────────────────────────────────────────────────────
@app.on_message(filters.command("about"))
async def about_cmd(client: Client, message: Message):
    await message.reply_text(Script.ABOUT_TXT, reply_to_message_id=message.id)
