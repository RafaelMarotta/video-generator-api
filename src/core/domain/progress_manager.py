from collections import defaultdict
from typing import Callable

class ProgressManager:
  def __init__(self):
    self.subscribers = defaultdict(list)

  def subscribe(self, pipeline_id: str, callback: Callable[[str], None]):
    print(f"🔔 Subscrito ao pipeline {pipeline_id}")
    self.subscribers[pipeline_id].append(callback)

  def unsubscribe(self, pipeline_id: str, callback: Callable[[str], None]):
    print(f"🔕 Removido do pipeline {pipeline_id}")
    if callback in self.subscribers[pipeline_id]:
      self.subscribers[pipeline_id].remove(callback)

  def publish(self, pipeline_id: str, message: str):
    print(f"📢 Enviando '{message}' para {len(self.subscribers[pipeline_id])} assinantes do pipeline {pipeline_id}")
    for callback in self.subscribers[pipeline_id]:
      callback(message)

progress_manager = ProgressManager()
