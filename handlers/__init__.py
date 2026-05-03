import logging
logger = logging.getLogger("MirrorNexus.Handlers")

logger.info("🛠 Registering handlers...")

try:
    from . import start
    from . import info
    from . import admin
    from . import session
    from . import settings
    from . import video
    from . import audio
    from . import document
    from . import url
    from . import mirror
    from . import upload
    logger.info("✅ All handlers registered successfully.")
except Exception as e:
    logger.error(f"❌ Error registering handlers: {e}", exc_info=True)
