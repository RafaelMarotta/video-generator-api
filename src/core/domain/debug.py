import os
from core.domain.pipeline import Step
from moviepy.video.VideoClip import ImageClip
from typing import Callable
from PIL import Image  # Vamos usar o PIL para abrir a imagem

class ExtractFrameStep(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        composite_clip = input["final_video"]

        # Se time_in_seconds não for passado, pega o último frame
        time_in_seconds: float = input.get("time_in_seconds")
        if time_in_seconds is None:
            time_in_seconds = max(0, composite_clip.duration - 0.05)  # tira 0.05s pra evitar erro

        # Captura o frame
        frame = composite_clip.get_frame(time_in_seconds)

        # Cria o ImageClip
        frame_clip = ImageClip(frame)

        # Salva
        output_path = input.get("output_path", "frame_debug.png")
        frame_clip.save_frame(output_path)

        # Abre a imagem no sistema
        try:
            Image.open(output_path).show()
        except Exception as e:
            print(f"Erro ao tentar abrir a imagem: {e}")

        # Atualiza o contexto
        context[self.name] = {
            "frame_clip": frame_clip,
            "frame_image_path": output_path,
        }
