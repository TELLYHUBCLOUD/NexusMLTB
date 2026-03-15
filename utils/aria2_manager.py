"""
Aria2c download manager wrapper using aria2p.
Handles direct links, magnets, torrent files, and NZB.
"""
import asyncio
import aria2p
from config import Config


class Aria2Manager:
    def __init__(self):
        self.api: aria2p.API | None = None

    def connect(self):
        self.api = aria2p.API(
            aria2p.Client(
                host=Config.ARIA2C_HOST,
                port=Config.ARIA2C_PORT,
                secret=Config.ARIA2C_SECRET,
            )
        )

    def add_download(self, url: str, download_dir: str, options: dict = None) -> str:
        opts = {"dir": download_dir, **(options or {})}
        download = self.api.add_uris([url], options=opts)
        return download.gid

    def add_torrent(self, torrent_path: str, download_dir: str) -> str:
        download = self.api.add_torrent(torrent_path, options={"dir": download_dir})
        return download.gid

    def add_magnet(self, magnet: str, download_dir: str) -> str:
        download = self.api.add_magnet(magnet, options={"dir": download_dir})
        return download.gid

    def get_download(self, gid: str):
        return self.api.get_download(gid)

    def cancel(self, gid: str):
        try:
            self.api.remove([self.api.get_download(gid)])
        except Exception:
            pass

    def get_stats(self, gid: str) -> dict:
        dl = self.get_download(gid)
        if not dl:
            return {}
        return {
            "name":        dl.name,
            "status":      dl.status,
            "total":       dl.total_length,
            "completed":   dl.completed_length,
            "speed":       dl.download_speed,
            "eta":         dl.eta.total_seconds() if dl.eta else 0,
            "path":        dl.dir,
            "is_complete": dl.is_complete,
            "has_error":   dl.has_failed,
            "error_msg":   dl.error_message or "",
        }

    async def wait_complete(self, gid: str, poll: float = 2.0):
        """Async wait loop until download completes or fails."""
        while True:
            stats = self.get_stats(gid)
            if stats.get("is_complete") or stats.get("has_error"):
                return stats
            await asyncio.sleep(poll)


aria2 = Aria2Manager()
