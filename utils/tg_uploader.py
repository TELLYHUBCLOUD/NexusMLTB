"""
Telegram uploader.
Uses user session string when available for 4 GB uploads.
Falls back to bot client for normal 2 GB uploads.
"""
import os
import time
import asyncio
from pathlib import Path
from pyrogram import Client
from pyrogram.types import Message
from bot.client import app
from bot.database import db
from config import Config
from utils.helpers import human_size, format_progress, split_file


async def _get_upload_client(user_id: int) -> Client:
    """Return a Pyrogram client: user session if available, else bot."""
    session_str = await db.get_session(user_id)
    if session_str:
        client = Client(
            f"user_{user_id}",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            session_string=session_str,
            in_memory=True,
        )
        await client.start()
        return client
    return app


class TelegramUploader:

    @staticmethod
    async def upload_file(
        source_msg: Message,
        file_path: str,
        caption: str = "",
        as_media: bool = False,
        thumb_path: str | None = None,
        chat_id: int | None = None,
    ) -> Message | None:
        """
        Upload file_path to Telegram.
        Splits automatically if > MAX_SPLIT_SIZE.
        Returns last sent Message or None on failure.
        """
        user_id = source_msg.from_user.id
        target  = chat_id or source_msg.chat.id
        size    = os.path.getsize(file_path)
        name    = Path(file_path).name

        # Status message
        status = await source_msg.reply_text(
            f"📤 <b>Uploading:</b> <code>{name}</code>\n"
            f"💾 Size: {human_size(size)}",
            reply_to_message_id=source_msg.id,
        )

        # Split if needed
        if size > Config.MAX_SPLIT_SIZE:
            parts = await split_file(file_path, Config.MAX_SPLIT_SIZE, f"{file_path}_parts")
            if not parts:
                await status.edit_text("❌ Failed to split file.")
                return None
            await status.edit_text(
                f"📤 Uploading <b>{len(parts)}</b> parts...\n💾 Total: {human_size(size)}"
            )
        else:
            parts = [file_path]

        client = await _get_upload_client(user_id)
        last_msg = None
        start_ts = time.time()

        for idx, part in enumerate(parts, 1):
            part_caption = caption
            if len(parts) > 1:
                part_caption = f"📦 Part {idx}/{len(parts)}\n{caption}"

            progress_data = {"last_edit": 0.0}

            async def _progress(current, total, _status=status, _data=progress_data):
                now = time.time()
                if now - _data["last_edit"] < 3:
                    return
                _data["last_edit"] = now
                speed = current / max(time.time() - start_ts, 1)
                eta   = (total - current) / max(speed, 1)
                text  = (
                    f"📤 <b>Uploading part {idx}/{len(parts)}</b>\n\n"
                    + format_progress(current, total, speed, eta)
                )
                try:
                    await _status.edit_text(text)
                except Exception:
                    pass

            try:
                part_size = os.path.getsize(part)
                if as_media and part.lower().endswith(
                    (".mp4", ".mkv", ".avi", ".webm", ".mov", ".mp3", ".flac", ".wav")
                ):
                    sent = await client.send_video(
                        target,
                        video=part,
                        caption=part_caption,
                        thumb=thumb_path,
                        progress=_progress,
                        reply_to_message_id=source_msg.id if idx == 1 else None,
                    )
                else:
                    sent = await client.send_document(
                        target,
                        document=part,
                        caption=part_caption,
                        thumb=thumb_path,
                        progress=_progress,
                        reply_to_message_id=source_msg.id if idx == 1 else None,
                    )
                last_msg = sent
                await db.inc_uploaded_bytes(part_size)
            except Exception as e:
                await status.edit_text(f"❌ Upload failed (part {idx}): {e}")
                return None

        # Stop user client if we started one
        if client is not app:
            await client.stop()

        elapsed = time.time() - start_ts
        m, s = divmod(int(elapsed), 60)
        await status.edit_text(
            f"✅ <b>Upload complete!</b>\n\n"
            f"📁 <code>{name}</code>\n"
            f"💾 {human_size(size)}\n"
            f"⏱ {m}m {s}s"
        )

        await db.inc_downloads()
        return last_msg
