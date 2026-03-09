
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, Dict, Any, List
from datetime import datetime

class MongoDBClient:
    def __init__(self, url: str, db_name: str = "synthhire"):
        self._client = AsyncIOMotorClient(url)
        self.db = self._client[db_name]

    async def close(self):
        self._client.close()

    async def save_exchange(self, exchange: Dict[str, Any]):
        return await self.db.exchanges.insert_one({
            **exchange,
            "created_at": datetime.utcnow()
        })

    async def get_session_exchanges(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self.db.exchanges.find(
            {"session_id": session_id}
        ).sort("exchange_number", 1)
        return await cursor.to_list(length=1000)

    async def save_whiteboard_snapshot(self, snapshot: Dict[str, Any]):
        return await self.db.whiteboard_snapshots.insert_one({
            **snapshot,
            "created_at": datetime.utcnow()
        })

    async def save_emotional_frame(self, frame: Dict[str, Any]):
        return await self.db.emotional_frames.insert_one({
            **frame,
            "created_at": datetime.utcnow()
        })

    async def get_session_emotions(self, session_id: str) -> List[Dict[str, Any]]:
        cursor = self.db.emotional_frames.find(
            {"session_id": session_id}
        ).sort("timestamp", 1)
        return await cursor.to_list(length=10000)

    async def get_company_patterns(self, company_slug: str) -> Optional[Dict[str, Any]]:
        return await self.db.company_patterns.find_one({"company_slug": company_slug})

    async def save_report_data(self, report: Dict[str, Any]):
        return await self.db.reports.insert_one({
            **report,
            "created_at": datetime.utcnow()
        })

    async def get_report(self, session_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.reports.find_one({"session_id": session_id})

    async def setup_indexes(self):
        await self.db.exchanges.create_index([("session_id", 1), ("exchange_number", 1)])
        await self.db.exchanges.create_index([("created_at", -1)])
        await self.db.whiteboard_snapshots.create_index([("session_id", 1)])
        await self.db.emotional_frames.create_index([("session_id", 1), ("timestamp", 1)])
        await self.db.company_patterns.create_index([("company_slug", 1)], unique=True)
        await self.db.reports.create_index([("session_id", 1)], unique=True)
