import json
import os
from abc import ABC, abstractmethod
from typing import Callable, List

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

    input_data = self.input_transformer(context) if self.input_transformer else {}
    self.execute(input_data, context)

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

class ForeachStep(Step):
  def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None, step: Step = None):
    super().__init__(name, description, input_transformer)
    self.step = step

  def execute(self, input: dict, context: dict):
    items = input.get("items", [])
    for item in items:
      context["current"] = item
      self.step.run(context)  # Mantém o write_debug do pai

class Pipeline:
  def __init__(self, name: str, description: str, steps: List[Step], write_debug: bool = False, debug_dir: str = "debug"):
    self.name = name
    self.description = description
    self.steps = steps
    self.write_debug = write_debug
    self.debug_dir = debug_dir

  def execute(self, context: dict):
    for step in self.steps:
      step.run(context, write_debug=self.write_debug, debug_dir=self.debug_dir)
