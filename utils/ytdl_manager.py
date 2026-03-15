"""
yt-dlp wrapper for downloading from YouTube and 1000+ sites.
"""
import os
import asyncio
import yt_dlp
from config import Config


class YTDLManager:

    @staticmethod
    def _base_opts(download_dir: str, progress_hook=None) -> dict:
        opts = {
            "outtmpl":         os.path.join(download_dir, "%(title)s.%(ext)s"),
            "restrictfilenames": True,
            "noplaylist":      False,
            "concurrent_fragment_downloads": 4,
            "retries":         3,
        }
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]
        return opts

    @staticmethod
    async def get_info(url: str) -> dict:
        """Fetch video info without downloading."""
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        loop = asyncio.get_event_loop()
        def _fetch():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        return await loop.run_in_executor(None, _fetch)

    @staticmethod
    async def download(
        url: str,
        download_dir: str,
        quality: str = "best",
        audio_only: bool = False,
        progress_hook=None,
    ) -> str | None:
        """
        Download URL. Returns path to downloaded file, or None on failure.
        quality: 'best', '1080', '720', '480', '360', 'audio'
        """
        opts = YTDLManager._base_opts(download_dir, progress_hook)

        if audio_only:
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]
        elif quality == "best":
            opts["format"] = "bestvideo+bestaudio/best"
        elif quality in ("1080", "720", "480", "360"):
            opts["format"] = (
                f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]"
            )
        else:
            opts["format"] = "bestvideo+bestaudio/best"

        downloaded_path: list[str] = []

        def _hook(d):
            if d["status"] == "finished":
                downloaded_path.append(d.get("filename", ""))
            if progress_hook:
                progress_hook(d)

        opts["progress_hooks"] = [_hook]

        loop = asyncio.get_event_loop()

        def _dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])

        try:
            await loop.run_in_executor(None, _dl)
        except Exception as e:
            return None

        return downloaded_path[0] if downloaded_path else None

    @staticmethod
    async def list_formats(url: str) -> list[dict]:
        info = await YTDLManager.get_info(url)
        return info.get("formats", []) if info else []


ytdl = YTDLManager()
