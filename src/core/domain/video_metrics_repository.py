# src/core/domain/video_metrics_repository.py
from core.commons.mongo import db
from typing import Dict, Any

class VideoMetricsRepository:
    def __init__(self):
        self.collection = db["video_metrics"]

    async def append_step(self, video_id: str, step_metrics: Dict[str, Any]):
        await self.collection.update_one(
            {"id": video_id},
            {"$push": {"steps": step_metrics}},
            upsert=True
        )

    async def get(self, video_id: str):
        return await self.collection.find_one({"id": video_id})
