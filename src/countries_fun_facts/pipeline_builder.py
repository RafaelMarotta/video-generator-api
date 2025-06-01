# src/countries_fun_facts/pipeline_builder.py

import os
from core.domain.pipeline import Pipeline, ForeachStep
from core.domain.caption_ai import GenerateCaptionWithSpeechInput, GenerateCaptionWithSpeechStep
from core.domain.image_ai import GenerateImageStep
from core.domain.video import ConcatenateVideoStep, ExportVideo, AddBackgroundMusicStep
from countries_fun_facts.fun_fact_prompt import GenerateFunFactInputStep
from countries_fun_facts.fun_facts_canvas import GenerateFunFactCanvas

# Caminho da fonte utilizada para legendas
font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"

# Diretório de saída do vídeo (pode ser setado via variável de ambiente)
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "")

def build_pipeline_fun_fact() -> Pipeline:
    # Subpipeline responsável por gerar 1 curiosidade completa
    single_fact_pipeline = Pipeline(
        name="generate_single_fact",
        description="Gera uma única curiosidade com imagem, legenda e áudio",
        steps=[
            GenerateImageStep(
                "generate_fact_image_step",
                "Gera e baixa a imagem da curiosidade",
                lambda context: {
                    "prompt": context["current"]["fact_image_prompt"],
                    "output_key": "fact_image_path",
                    "size": "1024x1024",
                    "use_tempfile": False,
                },
            ),
            GenerateCaptionWithSpeechStep(
                "generate_fun_fact_typing",
                "Gera a legenda animada e a narração da curiosidade",
                lambda context: GenerateCaptionWithSpeechInput(
                    text=context["current"]["fun_fact_text"],
                    max_lines=3,
                    max_chars_per_line=35,
                    font_size=55,
                    width=1000,
                    height=300,
                    font_path=font_path,
                    color="white",
                ),
            ),
            GenerateFunFactCanvas(
                "generate_fun_fact_canvas",
                "Composição visual da curiosidade com imagem e legenda",
                lambda context: {
                    "title_text": context["current"]["title_text"],
                    "font_path": font_path,
                    "number": context["current"]["number"],
                    "background_path": "src/countries_fun_facts/assets/background-fun-facts.png",
                    "typing_clip": context["generate_fun_fact_typing"]["typing_clip"],
                    "audio_clip": context["generate_fun_fact_typing"]["audio_clip"],
                    "fact_image": context["generate_fact_image_step"]["fact_image_path"],
                    "country_code": context["current"]["country_code"],
                },
            ),
        ]
    )

    # Pipeline principal com ForeachStep para n curiosidades
    return Pipeline(
        name="pipeline_fun_fact_country",
        description="Pipeline de geração de vídeo com curiosidades sobre um país",
        steps=[
            GenerateFunFactInputStep(
                "generate_fun_fact_input_step",
                "Gera o input completo para as curiosidades",
                lambda context: {
                    "country_name": context["text"],
                },
            ),
            ForeachStep(
                "create_facts",
                "Geração de vídeos para cada curiosidade",
                lambda context: {"items": context["generate_fun_fact_input_step"]["facts"]},
                single_fact_pipeline
            ),
            ConcatenateVideoStep(
                "concatenate_videos",
                "Concatena os vídeos gerados"
            ),
            AddBackgroundMusicStep(
                "add_background_music_step",
                "Adiciona música de fundo ao vídeo",
                lambda context: {
                    "final_video": context["concatenate_videos"]["final_video"],
                    "background_music_path": "src/countries_fun_facts/assets/background.mp3",
                },
            ),
            ExportVideo(
                "export_final_fun_fact",
                "Exporta o vídeo de curiosidade para um arquivo MP4",
                lambda context: {
                    "final_video": context["add_background_music_step"]["final_video"],
                    "output_path": os.path.join(OUTPUT_PATH, context["id"] + ".mp4"),
                },
            ),
        ]
    )
