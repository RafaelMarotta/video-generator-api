from core.commons.mongo import db
from typing import Dict, Any

class VideoRequestRepository:
    def __init__(self):
        self.collection = db["video_requests"]

    async def create(self, data: Dict[str, Any]):
        await self.collection.insert_one(data)

    async def update_status(self, video_id: str, status: str):
        await self.collection.update_one({"id": video_id}, {"$set": {"status": status}})

    async def update(self, video_id: str, update_data: Dict[str, Any]):
        await self.collection.update_one({"id": video_id}, {"$set": update_data})

    async def get(self, video_id: str):
        return await self.collection.find_one({"id": video_id}) 