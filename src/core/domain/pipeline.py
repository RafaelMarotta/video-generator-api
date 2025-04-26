from abc import ABC, abstractmethod
from typing import Callable


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


class Pipeline:
    def __init__(self, name: str, description: str, steps: list[Step]):
        self.name = name
        self.description = description
        self.steps = steps

    def execute(self, context: dict):
        for step in self.steps:
            step.run(context)
