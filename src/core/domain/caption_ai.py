import ast
import os
import tempfile
from moviepy import AudioFileClip, CompositeVideoClip, TextClip, concatenate_videoclips, ColorClip
from core.commons.openai import llm  # Importa a função genérica
from core.commons.audio_processor import generate_tts
from core.commons.font import get_valid_font_path
from core.commons.masks import rounded_mask
from core.domain.pipeline import Step
from core.domain.caption import GenerateCaptionWithSpeechInput
from typing import Callable

class GenerateCaptionAIStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: GenerateCaptionWithSpeechInput, context: dict):
        blocks = [" ".join(lines) for lines in self.generate_caption_blocks(input)]
        
        # 1. Gera o áudio completo
        full_audio = self.generate_audio_clip(" ".join(blocks))
        audio_duration = full_audio.duration

        # 2. Conta o total de caracteres dos blocos
        total_chars = sum(len(block) for block in blocks)

        text_clips = []

        # 3. Cria os TextClips com duração proporcional ao número de caracteres
        for block in blocks:
            block_chars = len(block)
            proportion = block_chars / total_chars
            block_duration = proportion * audio_duration - 0.35

            text_clip = self.format_text_clip(block, block_duration, input)
            text_clips.append(text_clip)

        # 4. Junta todos os TextClips
        typing_clip = concatenate_videoclips(text_clips)

        context[self.name] = {
            "typing_clip": typing_clip,
            "audio_clip": full_audio,
            "duration": audio_duration,
        }

    def format_text_clip(self, text: str, duration: float, input: GenerateCaptionWithSpeechInput):
        text_clip = TextClip(
            text=text,
            font_size=input.font_size,
            color=input.color,
            size=(input.width, input.height),
            font=get_valid_font_path(input.font_path),
            method="caption",
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

    def generate_audio_clip(self, block: str):
        audio_content = generate_tts(block)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            f.write(audio_content)
            audio_path = f.name
        audio_clip = AudioFileClip(audio_path)
        return audio_clip

    def generate_caption_blocks(self, input_data, expected_output=None):
        system_prompt = (
            "You are responsible for splitting a long text into multiple blocks for on-screen display. Follow these rules carefully:\n"
            "- Return a two-dimensional array (list of lists).\n"
            "- Each block must be a list of lines (strings).\n"
            "- Each line must not exceed `max_chars_per_line` characters.\n"
            "- Each block must not exceed `max_lines` lines.\n"
            "- Do not break words in the middle. Only break at spaces between words.\n"
            "- Prefer breaking after punctuation (periods, commas, dashes, semicolons) to maintain natural flow.\n"
            "- Do not insert explicit '\\n'. Each string in the list should represent a complete line.\n"
            "- Fill each block with as much text as possible without exceeding the limits.\n"
            "- If the text is too long, split into multiple blocks following the same rules.\n"
            "- Return ONLY the two-dimensional array (list of lists), without any explanation, prefix, or code block.\n"
            "- DO NOT wrap the output inside ``` markers or indicate any formatting like 'plaintext' or 'json'.\n"
            "- Output must be directly parsable as Python code."
        )

        user_input = (
            f"text: {input_data.text}\n"
            f"max_lines: {input_data.max_lines}\n"
            f"max_chars_per_line: {input_data.max_chars_per_line}"
        )

        def validate_response(output: str) -> bool:
            try:
                parsed = ast.literal_eval(output)
                return (
                    isinstance(parsed, list) and
                    all(isinstance(block, list) and all(isinstance(line, str) for line in block) for block in parsed)
                )
            except Exception:
                return False

        raw_blocks = llm(
            system_prompt=system_prompt,
            user_input=user_input,
            validate_response=validate_response,
            expected_output=expected_output,
            max_retries=3
        )

        if isinstance(raw_blocks, dict) and "error" in raw_blocks:
            raise ValueError(f"Failed to generate caption blocks: {raw_blocks['error']}")

        cleaned_blocks = ast.literal_eval(raw_blocks)
        return cleaned_blocks
