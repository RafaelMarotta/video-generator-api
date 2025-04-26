from core.domain.pipeline import Step
from moviepy import CompositeVideoClip, ImageClip
from typing import Callable

class GenerateQuestionCanvas(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        typing_clip = input["typing_clip"]
        audio_clip = input["audio_clip"]

        background = (
            ImageClip(input["background_path"])
            .resized((1080, 1920))
            .with_duration(typing_clip.duration)
        )

        top_margin = 220

        composite = CompositeVideoClip(
            [background, typing_clip.with_position(("center", top_margin))]
        )
        composite.audio = audio_clip
        context[self.name] = {
            "composite": composite,
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": top_margin + 200,
        }


class GenerateAnswerCanvas(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        typing_clip = input["typing_clip"]
        audio_clip = input["audio_clip"]
        top_margin = input.get("top_margin", 0) + 175

        last_frame = input.get("last_frame")
        background = (
            ImageClip(last_frame)
            .with_duration(typing_clip.duration)
            .resized((1080, 1920))
        )

        typing_clip = typing_clip.with_position(("center", top_margin))
        composite = CompositeVideoClip([background, typing_clip])
        composite.audio = audio_clip

        context[self.name] = {
            "composite": composite,
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": top_margin,
        }