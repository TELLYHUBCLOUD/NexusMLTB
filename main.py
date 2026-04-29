"""
Mirror Nexus Bot — Main Entry Point
Developer: @Venuboyy
"""
import asyncio
import os
import logging
from pathlib import Path
from aiohttp import web

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MirrorNexus")

# ── Ensure download dir exists ─────────────────────────────────────────────────
from config import Config
Path(Config.DOWNLOAD_DIR).mkdir(parents=True, exist_ok=True)

# ── Import bot & handlers (registers all decorators) ──────────────────────────
from bot.client import app
import handlers  # noqa: F401 — side-effect: registers all handlers

# ── Aria2 connection (non-fatal if not running) ────────────────────────────────
try:
    from utils.aria2_manager import aria2
    aria2.connect()
    logger.info("✅ Connected to aria2c RPC")
except Exception as e:
    logger.warning(f"⚠️ aria2c not available: {e} — direct downloads disabled")


# ── Heroku keep-alive web server ───────────────────────────────────────────────
async def health_check(request):
    return web.Response(text="Mirror Nexus Bot is running! 💎", status=200)


async def start_keepalive():
    """Start a minimal HTTP server on $PORT for Heroku health checks."""
    if not Config.IS_HEROKU:
        return
    web_app = web.Application()
    web_app.router.add_get("/", health_check)
    web_app.router.add_get("/health", health_check)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", Config.PORT)
    await site.start()
    logger.info(f"🌐 Keep-alive web server started on port {Config.PORT}")


# ── Bot startup message ────────────────────────────────────────────────────────
async def on_start():
    me = await app.get_me()
    logger.info(f"🚀 Mirror Nexus Bot started as @{me.username} (id={me.id})")
    logger.info(f"👷 Workers: {Config.WORKERS}")
    if Config.IS_HEROKU:
        logger.info(f"☁️ Running on Heroku (PORT={Config.PORT})")

    # Notify owner
    try:
        deploy_info = "\n☁️ Platform: Heroku" if Config.IS_HEROKU else "\n🖥 Platform: Local/VPS"
        await app.send_message(
            Config.OWNER_ID,
            f"🚀 <b>Mirror Nexus Bot started!</b>\n\n"
            f"👤 Bot: @{me.username}\n"
            f"👷 Workers: {Config.WORKERS}\n"
            f"🗄 DB: Connected"
            f"{deploy_info}",
        )
    except Exception:
        pass


# ── Run ────────────────────────────────────────────────────────────────────────
async def main():
    async with app:
        await on_start()
        await start_keepalive()
        logger.info("⚡ Bot is running. Press Ctrl+C to stop.")
        await asyncio.Event().wait()   # Keep running indefinitely


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user.")
