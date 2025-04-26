from core.commons.font import get_valid_font_path
from core.commons.image import add_rounded_border_to_image_clip
from core.domain.pipeline import Step
from moviepy.video.VideoClip import ImageClip, TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from typing import Callable

class GenerateFunFactCanvas(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        title_text = input["title_text"]
        typing_clip = input["typing_clip"]
        audio_clip = input["audio_clip"]

        background = (
            ImageClip(input["background_path"])
            .resized((1080, 1920))
            .with_duration(typing_clip.duration)
        )

        image_clip = (
            ImageClip("src/fun_facts/assets/example.png")
            .resized(width=700)
            .with_duration(typing_clip.duration)
        )

        title_clip = TextClip(
            text=title_text,
            font_size=80,
            size=(900, 200),
            method="caption",
            color="white",
            font=get_valid_font_path(input["font_path"]),
        ).with_duration(typing_clip.duration).with_position(("center", 100))

        img_with_border = add_rounded_border_to_image_clip(image_clip).with_position(
            ("center", 350)
        )

        caption_clip = typing_clip.with_position(("center", 1575))

        composite = CompositeVideoClip([background, title_clip, img_with_border, caption_clip])
        composite.audio = audio_clip

        context[self.name] = {
            "composite": composite,
            "final_frame": composite.get_frame(composite.duration - 0.05),
        }
