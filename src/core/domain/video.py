from core.domain.pipeline import Step
from moviepy import concatenate_videoclips, AudioFileClip, VideoClip, CompositeAudioClip, concatenate_audioclips
from typing import Callable

class ConcatenateVideoStep(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        video_clips: list[VideoClip] = context["composites"]
        final_clip = concatenate_videoclips(video_clips, method="compose")
        context[self.name] = {"final_video": final_clip}

class ExportVideo(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        final_video = input["final_video"]
        output_path = input.get("output_path", "output.mp4")
        final_video.write_videofile(output_path, fps=10, logger="bar")

class AddBackgroundMusicStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        final_video = input["final_video"]
        background_music_path = input["background_music_path"]

        # 1. Carrega o áudio de background
        music_clip = AudioFileClip(background_music_path)

        # 2. Calcula quantas vezes precisa repetir
        n_loops = int(final_video.duration // music_clip.duration) + 1
        repeated_music = concatenate_audioclips([music_clip] * n_loops)  # Corrigido aqui

        # 3. Garante que o áudio tenha a duração exata
        repeated_music = repeated_music.with_duration(final_video.duration)

        # 4. Se já existir áudio (ex: narração), combina
        if final_video.audio:
            final_audio = CompositeAudioClip([final_video.audio, repeated_music.with_volume_scaled(0.2)])
        else:
            final_audio = repeated_music

        # 5. Atualiza o áudio do vídeo
        final_video = final_video.with_audio(final_audio)

        context[self.name] = {
            "final_video": final_video
        }