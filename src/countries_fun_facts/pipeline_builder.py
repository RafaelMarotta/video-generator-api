# src/countries_fun_facts/pipeline_builder.py

import os
from fastapi.responses import FileResponse
from core.domain.upload import UploadYoutubeVideoStep
from countries_fun_facts.fun_fact_prompt import GenerateFunFactInputStep
from countries_fun_facts.fun_facts_canvas import GenerateFunFactCanvas
from core.domain.caption_ai import GenerateCaptionWithSpeechInput, GenerateCaptionWithSpeechStep
from core.domain.image_ai import GenerateImageStep
from core.domain.video import ConcatenateVideoStep, ExportVideo, AddBackgroundMusicStep
from core.domain.pipeline import Pipeline

font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "")


def build_pipeline_fun_fact() -> Pipeline:
    return Pipeline(
        "pipeline_fun_fact_country",
        "Pipeline de geração de vídeo com curiosidade sobre um país, forneça o nome do país a baixo:",
        steps=[
            GenerateFunFactInputStep(
                "generate_fun_fact_input_step",
                "Gera o input completo para a curiosidade",
                lambda context: {
                    "country_name": context["text"],
                    "number": context["number"],
                },
            ),
            GenerateImageStep(
                "generate_fact_image_step",
                "Gera e baixa a imagem da curiosidade",
                lambda context: {
                    "prompt": context["generate_fun_fact_input_step"][
                        "fact_image_prompt"
                    ],
                    "output_key": "fact_image_path",
                    "size": "1024x1024",
                    "use_tempfile": False,
                },
            ),
            GenerateCaptionWithSpeechStep(
                "generate_fun_fact_typing",
                "Gera a legenda animada e a narração da curiosidade",
                lambda context: GenerateCaptionWithSpeechInput(
                    text=context["generate_fun_fact_input_step"]["fun_fact_text"],
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
                    "title_text": context["generate_fun_fact_input_step"]["title_text"],
                    "font_path": font_path,
                    "number": context["generate_fun_fact_input_step"][
                        "number"
                    ],
                    "background_path": "src/countries_fun_facts/assets/background-fun-facts.png",
                    "typing_clip": context["generate_fun_fact_typing"]["typing_clip"],
                    "audio_clip": context["generate_fun_fact_typing"]["audio_clip"],
                    "fact_image": context["generate_fact_image_step"]["fact_image_path"],
                    # "fact_image": "debug.png",
                    "country_code": context["generate_fun_fact_input_step"][
                        "country_code"
                    ],
                },
            ),
            AddBackgroundMusicStep(
                "add_background_music_step",
                "Adiciona música de fundo ao vídeo",
                lambda context: {
                    "final_video": context["composites"][0],
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
            # ExtractFrameStep(
            #     "extract_final_frame",
            #     "Extrai o último frame do vídeo final",
            #     lambda context: {
            #         "final_video": context["add_background_music_step"]["final_video"]
            #     },
            # ),
            # UploadYoutubeVideoStep(
            #     "upload_final_video",
            #     "Upload do vídeo final para o YouTube",
            #     lambda context: {
            #         "title": context["generate_fun_fact_input_step"]["title_text"],
            #         "description": context["generate_fun_fact_input_step"][
            #             "fun_fact_text"
            #         ],
            #         "file_path": os.path.join(OUTPUT_PATH, context["id"] + ".mp4"),
            #         "category_id": "22",
            #         "privacy_status": "unlisted",
            #     },
            # ),
        ],
        write_debug=True,
    )
