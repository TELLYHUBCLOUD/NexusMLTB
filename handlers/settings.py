from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from bot.client import app
from bot.database import db
from bot.script import Script


def settings_keyboard(settings: dict) -> InlineKeyboardMarkup:
    upload_mode = settings.get("upload_mode", "File")
    rename_pref = settings.get("rename_prefix", "None")
    rename_suf  = settings.get("rename_suffix", "None")
    thumb_set   = "✅ Set" if settings.get("thumbnail") else "❌ None"
    caption_set = settings.get("caption_mode", "Default")

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📤 Upload Mode: {upload_mode}", callback_data="set_upload_mode")],
        [InlineKeyboardButton(f"📝 Prefix: {rename_pref}", callback_data="set_prefix"),
         InlineKeyboardButton(f"📝 Suffix: {rename_suf}",  callback_data="set_suffix")],
        [InlineKeyboardButton(f"🖼 Thumbnail: {thumb_set}", callback_data="set_thumb")],
        [InlineKeyboardButton(f"💬 Caption Mode: {caption_set}", callback_data="set_caption")],
        [InlineKeyboardButton("🗑 Clear Thumbnail",  callback_data="clear_thumb"),
         InlineKeyboardButton("🔄 Reset All",        callback_data="reset_settings")],
        [InlineKeyboardButton("❌ Close", callback_data="close_settings")],
    ])


@app.on_message(filters.command("settings"))
async def settings_cmd(client: Client, message: Message):
    uid = message.from_user.id
    settings = {
        "upload_mode":    await db.get_setting(uid, "upload_mode", "File"),
        "rename_prefix":  await db.get_setting(uid, "rename_prefix", "None"),
        "rename_suffix":  await db.get_setting(uid, "rename_suffix", "None"),
        "thumbnail":      await db.get_setting(uid, "thumbnail"),
        "caption_mode":   await db.get_setting(uid, "caption_mode", "Default"),
    }
    await message.reply_text(
        Script.SETTINGS_TXT,
        reply_markup=settings_keyboard(settings),
        reply_to_message_id=message.id,
    )


@app.on_callback_query(filters.regex("^set_upload_mode$"))
async def set_upload_mode(client: Client, cb: CallbackQuery):
    uid  = cb.from_user.id
    mode = await db.get_setting(uid, "upload_mode", "File")
    new  = "Media" if mode == "File" else "File"
    await db.set_setting(uid, "upload_mode", new)
    settings = {
        "upload_mode":   new,
        "rename_prefix": await db.get_setting(uid, "rename_prefix", "None"),
        "rename_suffix": await db.get_setting(uid, "rename_suffix", "None"),
        "thumbnail":     await db.get_setting(uid, "thumbnail"),
        "caption_mode":  await db.get_setting(uid, "caption_mode", "Default"),
    }
    await cb.message.edit_reply_markup(settings_keyboard(settings))
    await cb.answer(f"✅ Upload mode → {new}")


@app.on_callback_query(filters.regex("^reset_settings$"))
async def reset_settings(client: Client, cb: CallbackQuery):
    uid = cb.from_user.id
    for key in ["upload_mode", "rename_prefix", "rename_suffix", "thumbnail", "caption_mode"]:
        await db.set_setting(uid, key, None)
    await cb.answer("✅ Settings reset to defaults.")
    await cb.message.edit_reply_markup(settings_keyboard({
        "upload_mode":   "File",
        "rename_prefix": "None",
        "rename_suffix": "None",
        "thumbnail":     None,
        "caption_mode":  "Default",
    }))


@app.on_callback_query(filters.regex("^clear_thumb$"))
async def clear_thumb(client: Client, cb: CallbackQuery):
    await db.set_setting(cb.from_user.id, "thumbnail", None)
    await cb.answer("🗑 Thumbnail cleared.")


@app.on_callback_query(filters.regex("^close_settings$"))
async def close_settings(client: Client, cb: CallbackQuery):
    await cb.message.delete()
