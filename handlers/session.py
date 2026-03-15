"""
Session String Generator — lets users generate a Pyrogram session string
so the bot can upload files up to 4 GB on their behalf.
"""
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, ForceReply, InlineKeyboardMarkup, InlineKeyboardButton
from bot.client import app
from bot.database import db
from bot.script import Script
from config import Config

# Active session generation states: {user_id: {"step": ..., "phone": ..., "client": ...}}
_states: dict = {}


@app.on_message(filters.command("session") & filters.private)
async def session_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    existing = await db.get_session(user_id)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Regenerate", callback_data="gen_session"),
         InlineKeyboardButton("🗑 Delete Session", callback_data="del_session")],
    ]) if existing else InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Generate Session", callback_data="gen_session")],
    ])

    status = "✅ <b>You already have a session string saved.</b>\n\nYou can regenerate or delete it." \
        if existing else "ℹ️ <b>No session string saved yet.</b>\n\nGenerate one to enable 4GB uploads."

    await message.reply_text(
        f"<b>🔐 Session String Manager</b>\n\n{status}",
        reply_markup=keyboard,
        reply_to_message_id=message.id,
    )


@app.on_callback_query(filters.regex("^del_session$"))
async def del_session_cb(client, cb):
    await db.delete_session(cb.from_user.id)
    await cb.message.edit_text("🗑 Session deleted successfully.")


@app.on_callback_query(filters.regex("^gen_session$"))
async def gen_session_cb(client, cb):
    user_id = cb.from_user.id
    _states[user_id] = {"step": "phone"}
    await cb.message.edit_text(
        Script.SESSION_START_TXT,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="cancel_session")]
        ])
    )


@app.on_callback_query(filters.regex("^cancel_session$"))
async def cancel_session_cb(client, cb):
    _states.pop(cb.from_user.id, None)
    await cb.message.edit_text("❌ Session generation cancelled.")


@app.on_message(filters.private & ~filters.command([
    "start", "help", "about", "info", "stats", "broadcast",
    "ban", "unban", "settings", "cancel", "mirror", "leech",
    "status", "session"
]))
async def session_conversation(client: Client, message: Message):
    user_id = message.from_user.id
    state   = _states.get(user_id)
    if not state:
        return  # Not in session flow — pass to other handlers

    step = state.get("step")

    if step == "phone":
        phone = message.text.strip()
        if not phone.startswith("+"):
            await message.reply_text("❌ Invalid phone. Include country code. e.g. +919876543210",
                                     reply_to_message_id=message.id)
            return

        state["phone"] = phone
        state["step"]  = "code"

        # Create a temporary Pyrogram client for user login
        user_client = Client(
            f"session_{user_id}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            in_memory=True,
        )
        await user_client.connect()
        state["client"] = user_client

        try:
            sent_code = await user_client.send_code(phone)
            state["phone_code_hash"] = sent_code.phone_code_hash
            await message.reply_text(
                "📲 OTP sent! Enter the code you received:\n(Format: <code>1 2 3 4 5</code> or <code>12345</code>)",
                reply_to_message_id=message.id,
            )
        except Exception as e:
            await user_client.disconnect()
            _states.pop(user_id, None)
            await message.reply_text(f"❌ Error: {e}", reply_to_message_id=message.id)

    elif step == "code":
        code = message.text.strip().replace(" ", "")
        user_client: Client = state["client"]
        phone      = state["phone"]
        phone_hash = state["phone_code_hash"]

        try:
            await user_client.sign_in(phone, phone_hash, code)
        except Exception as e:
            err = str(e)
            if "SESSION_PASSWORD_NEEDED" in err:
                state["step"] = "password"
                await message.reply_text(
                    "🔒 Two-step verification enabled. Enter your password:",
                    reply_to_message_id=message.id,
                )
                return
            await user_client.disconnect()
            _states.pop(user_id, None)
            await message.reply_text(f"❌ Sign-in error: {e}", reply_to_message_id=message.id)
            return

        await _finish_session(message, user_id, user_client)

    elif step == "password":
        password    = message.text.strip()
        user_client: Client = state["client"]

        try:
            await user_client.check_password(password)
        except Exception as e:
            await user_client.disconnect()
            _states.pop(user_id, None)
            await message.reply_text(f"❌ Wrong password: {e}", reply_to_message_id=message.id)
            return

        await _finish_session(message, user_id, user_client)


async def _finish_session(message: Message, user_id: int, user_client: Client):
    try:
        session_str = await user_client.export_session_string()
        await user_client.disconnect()
        await db.save_session(user_id, session_str)
        _states.pop(user_id, None)

        await message.reply_text(
            "✅ <b>Session string saved successfully!</b>\n\n"
            "Your bot can now upload files up to <b>4 GB</b> using your Telegram account.\n\n"
            "⚠️ Keep your session safe. Use /session to manage it.",
            reply_to_message_id=message.id,
        )
    except Exception as e:
        _states.pop(user_id, None)
        await message.reply_text(f"❌ Failed to save session: {e}", reply_to_message_id=message.id)
