import time
from datetime import datetime, date
import motor.motor_asyncio
from config import Config


class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
        self.db     = self.client[Config.DB_NAME]
        self.users  = self.db.users
        self.stats  = self.db.stats
        self.sessions = self.db.sessions

    # ── Users ──────────────────────────────────────────────────
    async def add_user(self, user_id: int, user_data: dict):
        existing = await self.users.find_one({"user_id": user_id})
        if not existing:
            doc = {
                "user_id":    user_id,
                "first_name": user_data.get("first_name", ""),
                "username":   user_data.get("username", ""),
                "joined":     datetime.utcnow(),
                "join_date":  str(date.today()),
                "banned":     False,
            }
            await self.users.insert_one(doc)
            await self._inc_stat("total_downloads", 0)

    async def get_user(self, user_id: int):
        return await self.users.find_one({"user_id": user_id})

    async def total_users(self) -> int:
        return await self.users.count_documents({})

    async def users_today(self) -> int:
        today = str(date.today())
        return await self.users.count_documents({"join_date": today})

    async def all_user_ids(self):
        cursor = self.users.find({}, {"user_id": 1})
        return [doc["user_id"] async for doc in cursor]

    async def ban_user(self, user_id: int):
        await self.users.update_one({"user_id": user_id}, {"$set": {"banned": True}})

    async def unban_user(self, user_id: int):
        await self.users.update_one({"user_id": user_id}, {"$set": {"banned": False}})

    async def is_banned(self, user_id: int) -> bool:
        doc = await self.get_user(user_id)
        return doc.get("banned", False) if doc else False

    # ── Stats ──────────────────────────────────────────────────
    async def _inc_stat(self, key: str, val: int = 1):
        await self.stats.update_one(
            {"_id": "global"},
            {"$inc": {key: val}},
            upsert=True
        )

    async def inc_downloads(self):
        await self._inc_stat("total_downloads")

    async def inc_uploaded_bytes(self, size: int):
        await self._inc_stat("total_uploaded_bytes", size)

    async def get_global_stats(self) -> dict:
        doc = await self.stats.find_one({"_id": "global"})
        return doc or {}

    # ── Session Strings ────────────────────────────────────────
    async def save_session(self, user_id: int, session_string: str):
        await self.sessions.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "session": session_string, "updated": datetime.utcnow()}},
            upsert=True
        )

    async def get_session(self, user_id: int) -> str | None:
        doc = await self.sessions.find_one({"user_id": user_id})
        return doc["session"] if doc else None

    async def delete_session(self, user_id: int):
        await self.sessions.delete_one({"user_id": user_id})

    # ── User Settings ──────────────────────────────────────────
    async def get_setting(self, user_id: int, key: str, default=None):
        doc = await self.users.find_one({"user_id": user_id}, {key: 1})
        return doc.get(key, default) if doc else default

    async def set_setting(self, user_id: int, key: str, value):
        await self.users.update_one(
            {"user_id": user_id},
            {"$set": {key: value}},
            upsert=True
        )


db = Database()
