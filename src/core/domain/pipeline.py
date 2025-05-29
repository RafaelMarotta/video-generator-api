import json
import psutil
import time
import asyncio
from abc import ABC, abstractmethod
from typing import Callable, List
from core.domain.progress_manager import progress_manager
from core.domain.video_metrics_repository import VideoMetricsRepository

video_metrics_repo = VideoMetricsRepository()

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

    def run(self, context: dict):
        if "loop" not in context:
            raise RuntimeError(f"Missing 'loop' in context at step '{self.name}'! Você deve sempre passar o 'loop' no contexto em todas execuções de steps e pipelines!")
        pipeline_id = context.get("id")
        loop = context["loop"]
        input_data = self.input_transformer(context) if self.input_transformer else {}

        start_time = time.perf_counter()
        mem_before = psutil.Process().memory_info().rss / 1024**2

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

        asyncio.run_coroutine_threadsafe(
            video_metrics_repo.append_step(pipeline_id, step_metrics),
            loop
        )

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
            self.step.run(context)  # context é sempre o mesmo, inclui o loop

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
            self.step.run(context)  # context é sempre o mesmo, inclui o loop

class Pipeline(Step):
    def __init__(self, name: str, description: str, steps: List[Step]):
        super().__init__(name, description)
        self.steps = steps

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

    def run(self, context: dict):
        if "loop" not in context:
            raise RuntimeError(f"Missing 'loop' in context at step 'Pipeline: {self.name}'! Você deve sempre passar o 'loop' no contexto em todas execuções de steps e pipelines!")
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
                step.run(context)
                step_index += len(step.flatten_steps())
            elif isinstance(step, ForeachStep):
                input_data = step.input_transformer(context) if step.input_transformer else {}
                items = input_data.get("items", [])
                for i, item in enumerate(items):
                    context["current"] = item
                    publish_progress()
                    step.step.run(context)
                    step_index += 1
            else:
                publish_progress()
                step.run(context)
                step_index += 1
