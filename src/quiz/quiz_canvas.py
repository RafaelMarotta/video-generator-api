from cgitb import text
from core.domain import progress_bar
from core.domain.pipeline import Step
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, TextClip, VideoFileClip, vfx
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

        last_frame = {
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": top_margin + 320,
        }
        context["last_canvas"] = last_frame
        context[self.name] = last_frame


class GenerateAnswerCanvas(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        typing_clip = input["typing_clip"]
        audio_clip = input["audio_clip"]
        top_margin = input.get("top_margin", 0) + 170

        last_frame = input.get("last_frame")
        background = (
            ImageClip(last_frame)
            .with_duration(typing_clip.duration)
            .resized((1080, 1920))
        )

        typing_clip = typing_clip.with_position(("center", top_margin))
        composite = CompositeVideoClip([background, typing_clip])
        composite.audio = audio_clip
        
        if "create_answers" not in context:
            context["create_answers"] = {}

        if "typings" not in context["create_answers"] or context["create_answers"]["typings"] is None:
            context["create_answers"]["typings"] = []

        context["composites"] = context.get("composites", []) + [composite]
        context["create_answers"]["typings"].append(typing_clip)

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

        clock = (
            VideoFileClip("src/core/assets/clock-gif.gif", has_mask=True)
            .resized(height=80)  # Adjust height as needed
            .with_duration(progress_clip.duration)
        )

        progress_bar_x = (1080 - progress_clip.w) // 2
        progress_bar_y = 1480

        # Set positions
        progress_clip = progress_clip.with_position((progress_bar_x, progress_bar_y))
        clock = clock.with_position(("center", 175))

        # Create the composite video
        composite = CompositeVideoClip([background, progress_clip, clock])

        # Update context
        context["composites"] = context.get("composites", []) + [composite]
        context["last_canvas"] = {
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": 220,
        }

class GenerateCorrectAnswerCanvas(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
            super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        question_typing = input.get("question_typing")
        answers_clips = input.get("answers_clips")
        correct_answer_idx = input.get("correct_answer_idx")
        typing_clip = input["typing_clip"]

        background = (
            ImageClip(input["background_path"])
            .resized((1080, 1920))
            .with_duration(2)
        )

        question_typing = question_typing.with_duration(2)
        question_typing = question_typing.with_position(("center", 220))

        top_margin = 710  # Começa abaixo da pergunta
        gap = 170         # Espaçamento entre as respostas

        positioned_answers = []

        for idx, clip in enumerate(answers_clips):
            if idx == correct_answer_idx:
                audio_file = AudioFileClip("src/quiz/assets/correct.mp3")
                correct_clip = CompositeVideoClip([typing_clip]).with_effects(
                    [vfx.Blink(duration_on=0.35, duration_off=0.35)]
                ).with_position(("center", top_margin))
                correct_clip = correct_clip.with_audio(audio_file)
                positioned_answers.append(correct_clip)
            else:
                clip = clip.with_position(("center", top_margin)).without_audio()
                clip = clip.with_effects([vfx.Loop(duration=2)])
                positioned_answers.append(clip)

            top_margin += gap

        composite = CompositeVideoClip([background, question_typing] + positioned_answers).with_duration(2)

        context["composites"] = context.get("composites", []) + [composite]
        context["last_canvas"] = {
            "last_frame": composite.get_frame(composite.duration - 0.05),
            "top_margin": top_margin,
        }

