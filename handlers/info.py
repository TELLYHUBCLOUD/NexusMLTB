from pyrogram import Client, filters
from pyrogram.types import Message
from bot.client import app
from bot.script import Script
from config import Config


@app.on_message(filters.command("info"))
async def info_handler(client: Client, message: Message):
    # Allow /info @username or reply
    target = None
    if message.reply_to_message:
        target = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            target = await client.get_users(message.command[1])
        except Exception:
            await message.reply_text("❌ User not found.", reply_to_message_id=message.id)
            return
    else:
        target = message.from_user

    if not target:
        await message.reply_text("❌ Could not find user.", reply_to_message_id=message.id)
        return

    first_name = target.first_name or "None"
    last_name  = target.last_name  or "None"
    username   = f"@{target.username}" if target.username else "None"
    user_id    = target.id
    dc_id      = target.dc_id or "Unknown"
    is_premium = "✅ Yes" if getattr(target, "is_premium", False) else "❌ No"
    acc_type   = "Bot" if target.is_bot else "User"

    caption = Script.INFO_TXT.format(
        first_name=first_name,
        last_name=last_name,
        user_id=user_id,
        dc_id=dc_id,
        username=username,
        is_premium=is_premium,
        acc_type=acc_type,
    )

    # Try to fetch profile photo
    try:
        photos = client.get_chat_photos(target.id, limit=1)
        photo  = None
        async for p in photos:
            photo = p
            break

        if photo:
            await message.reply_photo(
                photo=photo.file_id,
                caption=caption,
                reply_to_message_id=message.id,
            )
        else:
            raise Exception("no photo")
    except Exception:
        await message.reply_text(caption, reply_to_message_id=message.id)
