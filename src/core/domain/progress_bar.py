import numpy as np
from moviepy import ImageSequenceClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw
from core.domain.pipeline import Step
from typing import Callable

class GenerateProgressBarStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        width, height = input.get('width', 800), input.get('height', 100)
        duration_per_frame = input.get('duration_per_frame', 0.5)

        border_color = (200, 200, 200, 255)
        progress_color = (0, 204, 0, 255)
        border_radius = 50
        border_thickness = 6
        audio_path = input.get('audio_path', 'src/core/assets/clock.wav')

        def draw_progress_bar(progress):
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))  # Fundo transparente
            draw = ImageDraw.Draw(img)

            draw.rounded_rectangle(
                [(0, 0), (width-1, height-1)],
                radius=border_radius,
                outline=border_color,
                width=border_thickness
            )

            inner_width = int((width - 2 * border_thickness) * progress)
            if inner_width > 0:
                draw.rounded_rectangle(
                    [(border_thickness, border_thickness), (border_thickness + inner_width, height - border_thickness)],
                    radius=border_radius,
                    fill=progress_color
                )

            return np.array(img)

        frames = [draw_progress_bar(i / 10.0) for i in range(1, 11)]

        clips = []
        for i, frame in enumerate(frames):
            clip = ImageSequenceClip([frame], durations=[duration_per_frame])
            if i < len(frames) - 2:
                audio_clip = AudioFileClip(audio_path)
                clip = clip.with_audio(audio_clip)
            clips.append(clip)

        progress_clip = concatenate_videoclips(clips)

        context[self.name] = {
            "progress_clip": progress_clip,
            "duration": progress_clip.duration
        }
