import re
import tempfile
import textwrap
from core.commons.font import get_valid_font_path
from core.commons.masks import rounded_mask
from core.domain.pipeline import Step
from core.commons.audio_processor import generate_tts, create_silence
from moviepy import concatenate_videoclips, concatenate_audioclips, TextClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.video.VideoClip import ColorClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from typing import Callable, Optional
from dataclasses import dataclass

COLOR_PRESETS = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
}


def parse_color(color):
    if isinstance(color, str):
        return COLOR_PRESETS.get(color.lower(), (0, 0, 0))
    return color

@dataclass
class BackgroundConfig:
    color: Optional[str] = None 
    padding: int = 30
    width: Optional[int] = None
    height: Optional[int] = None
    opacity: float = 1.0

@dataclass
class GenerateCaptionInput:
    text: str
    font_path: str = ""
    font_size: int = 70
    color: str = "white"
    background: Optional[BackgroundConfig] = None
    max_lines: int = 2
    max_chars_per_line: int = 20
    duration_per_letter: float = 0.20
    effect: str = ""

@dataclass
class GenerateCaptionWithSpeechInput(GenerateCaptionInput):
    pass

class GenerateCaptionStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: GenerateCaptionInput, context: dict):
        text_clips = self.create_text_clips(input)
        typing_clip = concatenate_videoclips(text_clips)
        total_duration = sum([clip.duration for clip in text_clips])

        context[self.name] = {
            "typing_clip": typing_clip,
            "duration": total_duration,
        }

    def create_text_clips(self, input: GenerateCaptionInput):
        return self.create_typing_clips(input) if input.effect == "typing" else self.generate_text_clips(input)

    def generate_text_clips(self, input: GenerateCaptionInput):
        words = input.text.strip().split()
        blocks = []
        current_block = ""

        for word in words:
            test_block = f"{current_block} {word}".strip()
            lines = self.wrap_text_by_words(test_block, input.max_chars_per_line)
            if len(lines) <= input.max_lines:
                current_block = test_block
            else:
                blocks.append(current_block)
                current_block = word

        if current_block:
            blocks.append(current_block)

        text_clips = []
        for i, block in enumerate(blocks):
            final_text = self.align_center("\n".join(self.wrap_text_by_words(block, input.max_chars_per_line)), input.max_chars_per_line)
            clip_duration = input.duration_per_letter * len(block.replace(" ", ""))
            clip = self.format_text_clip(final_text, clip_duration, input)
            text_clips.append(clip)

        return text_clips

    def wrap_text_by_words(self, text_so_far: str, max_chars: int):
        text_so_far = re.sub(r"([‘’'\"“”]) (?=\w)", r"\1", text_so_far)
        words = text_so_far.split()
        lines = []
        current_line = ""

        for word in words:
            if len(word) > max_chars:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                broken_parts = textwrap.wrap(word, width=max_chars, break_long_words=True, break_on_hyphens=False)
                for i, part in enumerate(broken_parts):
                    if i < len(broken_parts) - 1:
                        lines.append(part + "-")
                    else:
                        current_line = part
            else:
                if len(current_line + " " + word) <= max_chars:
                    current_line = f"{current_line} {word}".strip()
                else:
                    lines.append(current_line)
                    current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def align_center(self, text: str, max_chars_per_line: int):
        lines = text.split("\n")
        aligned = []

        for line in lines:
            stripped_line = line.strip()
            pad_total = max_chars_per_line - len(stripped_line)
            pad_left = pad_total // 2 if pad_total > 0 else 0
            aligned.append(" " * pad_left + stripped_line)

        return "\n".join(aligned)

    def format_text_clip(self, text: str, duration: float, input: GenerateCaptionInput):
        text_clip = TextClip(
            text=text,
            font_size=input.font_size,
            color=input.color,
            font=get_valid_font_path(input.font_path),
            method="label",
        ).with_duration(duration)

        if input.background and input.background.color:
            rgb = parse_color(input.background.color)
            padding = input.background.padding
            w, h = text_clip.size
            width = input.background.width or w
            height = input.background.height or h
            bg = ColorClip(size=(width + padding * 2, height + padding * 2), color=rgb).with_opacity(input.background.opacity)
            mask_array = rounded_mask(bg.size, radius=40)

            bg = bg.with_mask(mask_array)
            bg = bg.with_duration(duration)
            return CompositeVideoClip([bg, text_clip.with_position((padding, padding))])
        else:
            return text_clip

    def create_typing_clips(self, input: GenerateCaptionInput):
        text_clips = []
        previous_lines = []

        for i in range(len(input.text)):
            if input.text[i] in [" ", "\n"]:
                continue
            partial_text = input.text[:i + 1]
            lines = self.wrap_text_by_words(partial_text.strip(), input.max_chars_per_line)
            final_text = self.align_center("\n".join(lines), input.max_chars_per_line)
            clip = self.format_text_clip(final_text, input.duration_per_letter, input)

            if previous_lines and len(lines) < len(previous_lines):
                clip = clip.with_duration(clip.duration)

            text_clips.append(clip)
            previous_lines = lines

        return text_clips


class GenerateCaptionStepWithSpeech(GenerateCaptionStep):
    def execute(self, input: GenerateCaptionWithSpeechInput, context: dict):
        text_clips = []
        audio_clips = []

        words = input.text.strip().split()
        current_block = ""
        blocks = []

        for word in words:
            test_block = f"{current_block} {word}".strip()
            lines = self.wrap_text_by_words(test_block, input.max_chars_per_line)
            if len(lines) <= input.max_lines:
                current_block = test_block
            else:
                blocks.append(current_block)
                current_block = word

        if current_block:
            blocks.append(current_block)

        for block in blocks:
            audio_clip = self.generate_audio_clip(block, audio_clips)
            text_clips.extend(self.create_block_clips(block, input, audio_clip))

        typing_clip = concatenate_videoclips(text_clips)
        full_audio = concatenate_audioclips(audio_clips)

        context[self.name] = {
            "typing_clip": typing_clip,
            "audio_clip": full_audio,
        }

    def generate_audio_clip(self, block: str, audio_clips: list):
        audio_content = generate_tts(block)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_content)
            audio_path = f.name
        audio_clip = AudioFileClip(audio_path)
        audio_clips.append(audio_clip)
        return audio_clip

    def create_block_clips(self, block: str, input: GenerateCaptionWithSpeechInput, audio_clip):
        input.text = block
        if input.effect == "typing":
            total_letters = len([c for c in block if c not in [" ", "\n"]])
            input.duration_per_letter = max(audio_clip.duration / max(total_letters, 1), 0.07)
            return self.create_typing_clips(input)
        else:
            return self.create_static_clip(block, input, audio_clip.duration)

    def create_static_clip(self, block: str, input: GenerateCaptionWithSpeechInput, duration: float):
        lines = self.wrap_text_by_words(block.strip(), input.max_chars_per_line)
        final_text = self.align_center("\n".join(lines), input.max_chars_per_line)
        return [self.format_text_clip(final_text, duration, input)]
