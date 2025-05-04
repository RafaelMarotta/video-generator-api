from typing import Callable, Dict, List
from core.domain.pipeline import Pipeline
from countries_fun_facts.pipeline_builder import build_pipeline_fun_fact

class PipelineFactory:
  def __init__(self):
    self._registry: Dict[str, Callable[[], Pipeline]] = {}
    self._descriptions: Dict[str, str] = {}

  def register(self, name: str, builder: Callable[[], Pipeline]):
    self._registry[name] = builder
    try:
      pipeline = builder()
      self._descriptions[name] = pipeline.description
    except Exception:
      self._descriptions[name] = "No description available"

  def create(self, name: str) -> Pipeline:
    if name not in self._registry:
      raise ValueError(f"Pipeline '{name}' not found.")
    return self._registry[name]()

  def list_pipelines(self) -> List[Dict[str, str]]:
    return [
      {"name": name, "description": desc}
      for name, desc in self._descriptions.items()
    ]
    
pipeline_factory = PipelineFactory()
pipeline_factory.register("pipeline_fun_fact_country", build_pipeline_fun_fact)
