# src/core/domain/video_metrics_repository.py
from core.commons.mongo import db
from typing import Dict, Any, List

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

    async def get_all(self) -> List[Dict[str, Any]]:
        try:
            print("Starting get_all metrics query...")
            cursor = self.collection.find({})
            metrics = await cursor.to_list(length=None)
            print(f"Retrieved {len(metrics)} metrics from database")
            
            # Remove _id from each document
            for metric in metrics:
                if metric and "_id" in metric:
                    metric.pop("_id", None)
            
            return metrics
        except Exception as e:
            print(f"Error in get_all: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise
