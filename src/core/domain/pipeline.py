from abc import ABC, abstractmethod
from typing import Callable, List

class Step(ABC):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        self.name = name
        self.description = description
        self.input_transformer = input_transformer

    def run(self, context: dict):
        print(f"Running step {self.name}")
        input_data = self.input_transformer(context) if self.input_transformer else {}
        self.execute(input_data, context)

    @abstractmethod
    def execute(self, input: dict, context: dict):
        pass

class ForeachStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = [], step: Step = None):
        super().__init__(name, description, input_transformer)
        self.step = step
        
    def execute(self, input: dict, context: dict):
        for item in input["items"]:
            context["current"] = item
            self.step.execute(context)

class Pipeline:
    def __init__(self, name: str, description: str, steps: list[Step]):
        self.name = name
        self.description = description
        self.steps = steps

    def execute(self, context: dict):
        for step in self.steps:
            step.run(context)