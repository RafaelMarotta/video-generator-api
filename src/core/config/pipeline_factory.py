from typing import Callable, Dict, List
from core.domain.pipeline import Pipeline
from countries_fun_facts.pipeline_builder import build_pipeline_fun_fact
from quiz.pipeline_builder import build_pipeline_quiz


class PipelineFactory:
    def __init__(self):
        self._registry: Dict[str, Callable[[], Pipeline]] = {}
        self._pipelines: Dict[str, str] = {}
        self._tones = [
            {
                "description": "Tom Engraçadinho",
                "tone_prompt": "You are a playful and humorous host who loves making people laugh. Your tone is light and fun, with clever jokes and playful comments. You find humor in everything but keep it tasteful and accessible. You use wordplay, funny observations, and light-hearted comments to make the content entertaining while still being informative."
            },
            {
                "description": "Tom Sério",
                "tone_prompt": "You are a professional and knowledgeable host who takes the content seriously. Your tone is clear, formal, and authoritative, but not dry or boring. You focus on delivering accurate information in a dignified and respectful way, using precise language and maintaining a professional demeanor throughout."
            },
            {
                "description": "Tom Animado",
                "tone_prompt": "You are an enthusiastic and energetic host who brings excitement to every topic. Your tone is dynamic and engaging, full of energy and passion. You use expressive language, show genuine excitement about the content, and maintain high energy throughout. You make everything sound exciting and interesting, using enthusiasm to keep everyone engaged."
            }
        ]

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
                "tones": self._tones
            }
        except Exception:
            self._pipelines[name] = {
                "name": name,
                "description": "No description available",
                "placeholder": "No placeholder available",
                "tones": self._tones
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
pipeline_factory.register(
    "Video quiz",
    "Filmes de comédia",
    "Número de questões",
    build_pipeline_quiz
)
