import json
import os
import time
import psutil
from abc import ABC, abstractmethod
from typing import Callable, List
from core.domain.progress_manager import progress_manager


def make_serializable(obj):
  try:
    json.dumps(obj)
    return obj
  except (TypeError, OverflowError):
    return str(obj)


class Step(ABC):
  def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
    self.name = name
    self.description = description
    self.input_transformer = input_transformer

  def run(self, context: dict, write_debug: bool = False, debug_dir: str = "debug"):
    print(f"{self.description}")
    pipeline_id = context.get("id")
    input_data = self.input_transformer(context) if self.input_transformer else {}

    start_time = time.perf_counter()
    mem_before = psutil.Process().memory_info().rss / 1024**2  # em MB

    self.execute(input_data, context)

    end_time = time.perf_counter()
    mem_after = psutil.Process().memory_info().rss / 1024**2

    duration = round(end_time - start_time, 3)
    memory_mb = round(mem_after - mem_before, 2)

    step_metrics = {
      "step": self.name,
      "description": self.description,
      "duration_sec": duration,
      "memory_diff_mb": memory_mb
    }

    context.setdefault("metrics", []).append(step_metrics)

    # Append persistente no arquivo de métricas
    metrics_dir = "metrics"
    os.makedirs(metrics_dir, exist_ok=True)
    metrics_path = os.path.join(metrics_dir, f"{pipeline_id}.json")

    if os.path.exists(metrics_path):
      with open(metrics_path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    else:
      existing = {
        "id": pipeline_id,
        "steps": []
      }

    existing["steps"].append(step_metrics)

    with open(metrics_path, "w", encoding="utf-8") as f:
      json.dump(existing, f, indent=2)

    if write_debug:
      os.makedirs(debug_dir, exist_ok=True)
      debug_data = {
        "input": self._make_debug_serializable(input_data),
        "context": self._make_debug_serializable(context.copy())
      }
      debug_path = os.path.join(debug_dir, f"{self.name}.json")
      with open(debug_path, "w", encoding="utf-8") as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)

  def _make_debug_serializable(self, data):
    if isinstance(data, dict):
      return {k: self._make_debug_serializable(v) for k, v in data.items()}
    elif isinstance(data, list):
      return [self._make_debug_serializable(v) for v in data]
    else:
      return make_serializable(data)

  @abstractmethod
  def execute(self, input: dict, context: dict):
    pass


class LoopStep(Step):
  def __init__(self, name: str, description: str, times: int = 1, step: Step = None):
    super().__init__(name, description)
    self.times = times
    self.step = step

  def flatten_steps(self):
    return self.step.flatten_steps() if isinstance(self.step, Pipeline) else [self.step]

  def execute(self, input: dict, context: dict):
    n = context.get("n", self.times)
    for i in range(n):
      context["loop_index"] = i
      self.step.run(context)


class ForeachStep(Step):
  def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None, step: Step = None):
    super().__init__(name, description, input_transformer)
    self.step = step

  def flatten_steps(self):
    return self.step.flatten_steps() if isinstance(self.step, Pipeline) else [self.step]

  def execute(self, input: dict, context: dict):
    items = input.get("items", [])
    for i, item in enumerate(items):
      context["current"] = item
      self.step.run(context)


class Pipeline(Step):
  def __init__(self, name: str, description: str, steps: List[Step], write_debug: bool = False, debug_dir: str = "debug"):
    super().__init__(name, description)
    self.steps = steps
    self.write_debug = write_debug
    self.debug_dir = debug_dir

  def execute(self, input: dict, context: dict):
    pass

  def flatten_steps(self) -> List[Step]:
    flat = []
    for step in self.steps:
      if isinstance(step, Pipeline):
        flat.extend(step.flatten_steps())
      elif isinstance(step, ForeachStep):
        flat.extend(step.flatten_steps())
      else:
        flat.append(step)
    return flat

  def run(self, context: dict, write_debug: bool = False, debug_dir: str = "debug"):
    pipeline_id = context.get("id")
    flat_steps = self.flatten_steps()
    step_index = 0

    def publish_progress():
      progress_manager.publish(pipeline_id, json.dumps({
        "executed": [
          {"name": s.name, "description": s.description}
          for s in flat_steps[:step_index]
        ],
        "running": [
          {"name": s.name, "description": s.description}
          for s in flat_steps[step_index:]
        ]
      }))

    for step in self.steps:
      if isinstance(step, Pipeline):
        step.run(context, write_debug=self.write_debug, debug_dir=self.debug_dir)
        step_index += len(step.flatten_steps())

      elif isinstance(step, ForeachStep):
        input_data = step.input_transformer(context) if step.input_transformer else {}
        items = input_data.get("items", [])
        for i, item in enumerate(items):
          context["current"] = item
          publish_progress()
          step.step.run(context, write_debug=self.write_debug, debug_dir=self.debug_dir)
          step_index += 1

      else:
        publish_progress()
        step.run(context, write_debug=self.write_debug, debug_dir=self.debug_dir)
        step_index += 1
