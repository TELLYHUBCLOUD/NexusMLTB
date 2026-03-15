"""
Third-party upload helpers: GoFile, PixelDrain, BuzzHeavier.
"""
import aiohttp
import aiofiles
from pathlib import Path


# ── GoFile ─────────────────────────────────────────────────────────────────────
async def upload_gofile(file_path: str) -> str | None:
    """Upload to GoFile.io — returns download URL or None."""
    try:
        # Get best server
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.gofile.io/getServer") as r:
                data = await r.json()
                server = data["data"]["server"]

            url  = f"https://{server}.gofile.io/uploadFile"
            name = Path(file_path).name
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            form = aiohttp.FormData()
            form.add_field("file", content, filename=name)
            async with session.post(url, data=form) as r:
                resp = await r.json()
                if resp.get("status") == "ok":
                    return resp["data"].get("downloadPage")
    except Exception as e:
        print(f"GoFile error: {e}")
    return None


# ── PixelDrain ─────────────────────────────────────────────────────────────────
async def upload_pixeldrain(file_path: str) -> str | None:
    """Upload to PixelDrain — returns download URL or None."""
    try:
        name = Path(file_path).name
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            form = aiohttp.FormData()
            form.add_field("file", content, filename=name)
            async with session.post("https://pixeldrain.com/api/file/", data=form) as r:
                resp = await r.json()
                if "id" in resp:
                    return f"https://pixeldrain.com/u/{resp['id']}"
    except Exception as e:
        print(f"PixelDrain error: {e}")
    return None


# ── BuzzHeavier ────────────────────────────────────────────────────────────────
async def upload_buzzheavier(file_path: str) -> str | None:
    """Upload to BuzzHeavier — returns download URL or None."""
    try:
        name = Path(file_path).name
        async with aiohttp.ClientSession() as session:
            async with aiofiles.open(file_path, "rb") as f:
                content = await f.read()
            form = aiohttp.FormData()
            form.add_field("file", content, filename=name)
            async with session.post("https://buzzheavier.com/api/upload", data=form) as r:
                resp = await r.json()
                return resp.get("url")
    except Exception as e:
        print(f"BuzzHeavier error: {e}")
    return None
