from core.domain import progress_bar
from core.domain.pipeline import Step
from moviepy import CompositeVideoClip, ImageClip, VideoFileClip
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
        context["composites"] = context.get("composites", []) + [composite]

        context["last_canvas"] = {
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": top_margin + 200,
        }


class GenerateAnswerCanvas(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        typing_clip = input["typing_clip"]
        audio_clip = input["audio_clip"]
        top_margin = input.get("top_margin", 0) + 220

        last_frame = input.get("last_frame")
        background = (
            ImageClip(last_frame)
            .with_duration(typing_clip.duration)
            .resized((1080, 1920))
        )

        typing_clip = typing_clip.with_position(("center", top_margin))
        composite = CompositeVideoClip([background, typing_clip])
        composite.audio = audio_clip

        context["composites"] = context.get("composites", []) + [composite]

        context["last_canvas"] = {
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": top_margin,
        }

class GenerateProgressBarCanvas(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        progress_clip = input["progress_clip"]

        last_frame = input.get("last_frame")
        background = (
            ImageClip(last_frame)
            .resized((1080, 1920))
            .with_duration(progress_clip.duration)
        )

        # Load and configure the clock image
        clock = (
            VideoFileClip("src/core/assets/clock-gif.gif", has_mask=True)
            .resized(height=80)  # Adjust height as needed
            .with_duration(progress_clip.duration)
        )

        progress_bar_x = (1080 - progress_clip.w) // 2
        progress_bar_y = 1500
        clock_x = progress_bar_x - clock.w + 100  # 20 pixels gap between clock and progress bar
        clock_y = progress_bar_y + (progress_clip.h - clock.h) // 2

        # Set positions
        progress_clip = progress_clip.with_position((progress_bar_x, progress_bar_y))
        clock = clock.with_position((clock_x, clock_y))

        # Create the composite video
        composite = CompositeVideoClip([background, progress_clip, clock])

        # Update context
        context["composites"] = context.get("composites", []) + [composite]
        context["last_canvas"] = {
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": 220,
        }