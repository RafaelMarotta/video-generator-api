from typing import Callable, Dict, List
from core.domain.pipeline import Pipeline
from countries_fun_facts.pipeline_builder import build_pipeline_fun_fact
from quiz.pipeline_builder import build_pipeline_quiz


class PipelineFactory:
    def __init__(self):
        self._registry: Dict[str, Callable[[], Pipeline]] = {}
        self._pipelines: Dict[str, Dict[str, str]] = {}

    def register(
        self,
        name: str,
        placeholder: str,
        numberLabel: str,
        builder: Callable[[], Pipeline],
    ):
        self._registry[name] = builder
        try:
            pipeline = builder()
            self._pipelines[name] = {
                "name": name,
                "description": pipeline.description,
                "placeholder": placeholder,
                "numberLabel": numberLabel,
            }
        except Exception:
            self._pipelines[name] = {
                "name": name,
                "description": "No description available",
                "placeholder": "No placeholder available",
            }

    def create(self, name: str) -> Pipeline:
        if name not in self._registry:
            raise ValueError(f"Pipeline '{name}' not found.")
        return self._registry[name]()

    def list_pipelines(self) -> List[Dict[str, str]]:
        return list(self._pipelines.values())


# Registra as pipelines
pipeline_factory = PipelineFactory()
pipeline_factory.register(
    "Curiosidades sobre um país",
    "Baile em assunção",
    "Quantidade de curiosidades",
    build_pipeline_fun_fact,
)
pipeline_factory.register("Video quiz", "Filmes de comédia", None, build_pipeline_quiz)
