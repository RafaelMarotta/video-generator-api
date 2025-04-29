from doctest import debug
from core.commons.openai import generate_image_from_text, download_image_from_url
from core.domain.upload import UploadYoutubeVideoStep
from countries_fun_facts.fun_fact_prompt import GenerateFunFactInputStep
from countries_fun_facts.fun_facts_canvas import GenerateFunFactCanvas
from core.domain.caption import (
    GenerateCaptionStepWithSpeech,
    GenerateCaptionWithSpeechInput,
)
from core.domain.caption_ai import GenerateCaptionAIStep
from core.domain.image_ai import GenerateImageStep
from core.domain.video import (
    ConcatenateVideoStep,
    ExportVideo,
    AddBackgroundMusicStep,
) 
from core.domain.debug import ExtractFrameStep
from core.domain.pipeline import Pipeline

font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"

# 1. Step para gerar o input
generate_fun_fact_input_step = GenerateFunFactInputStep(
    "generate_fun_fact_input_step",
    "Gera o input completo para a curiosidade",
    lambda context: {
        "country_name": context["country_name"],
        "fact_number": context["fact_number"],
    },
)

# 2. Step para gerar a imagem
generate_fact_image_step = GenerateImageStep(
    "generate_fact_image_step",
    "Gera e baixa a imagem da curiosidade",
    lambda context: {
        "prompt": context["generate_fun_fact_input_step"]["fact_image_prompt"],
        "output_key": "fact_image_path",
        "size": "1024x1024",
        "use_tempfile": False,
    },
)

# 3. Step para gerar a legenda + narração
generate_fun_fact_typing = GenerateCaptionAIStep(
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
)

# 4. Step para montar o canvas
generate_fun_fact_canvas = GenerateFunFactCanvas(
    "generate_fun_fact_canvas",
    "Composição visual da curiosidade com imagem e legenda",
    lambda context: {
        "title_text": context["generate_fun_fact_input_step"]["title_text"],
        "font_path": font_path,
        "fact_number": context["generate_fun_fact_input_step"]["fact_number"],
        "background_path": "src/countries_fun_facts/assets/background-fun-facts.png",
        "typing_clip": context["generate_fun_fact_typing"]["typing_clip"],
        "audio_clip": context["generate_fun_fact_typing"]["audio_clip"],
        # "fact_image": context["generate_fact_image_step"]["fact_image_path"],
        "fact_image": "debug.png",
        "country_code": context["generate_fun_fact_input_step"]["country_code"],
    },
)

# 5. Step para adicionar música de fundo
add_background_music_step = AddBackgroundMusicStep(
    "add_background_music_step",
    "Adiciona música de fundo ao vídeo",
    lambda context: {
        "final_video": context["composites"][0],
        "background_music_path": "src/countries_fun_facts/assets/background.mp3",
    },
)

# 6. Step para exportar o vídeo
export_final_fun_fact = ExportVideo(
    "export_final_fun_fact",
    "Exporta o vídeo de curiosidade para um arquivo MP4",
    lambda context: {
        "final_video": context["add_background_music_step"]["final_video"],
        "output_path": "output.mp4",
    },
)

# 7. Step para extrair o último frame
extract_final_frame = ExtractFrameStep(
    "extract_final_frame",
    "Extrai o último frame do vídeo final",
    lambda context: {
        "final_video": context["add_background_music_step"]["final_video"]
    },
)

# 8. Step para upload no YouTube
upload_final_video = UploadYoutubeVideoStep(
    "upload_final_video",
    "Upload do vídeo final para o YouTube",
    lambda context: {
        "title": context["generate_fun_fact_input_step"]["title_text"],
        "description": context["generate_fun_fact_input_step"]["fun_fact_text"],
        "file_path": "output.mp4",
        "category_id": "22",
        "privacy_status": "unlisted",
    },
)

# 9. Define a pipeline final
pipeline_fun_fact = Pipeline(
    "pipeline_fun_fact_country",
    "Pipeline de geração de vídeo com curiosidade sobre um país",
    [
        generate_fun_fact_input_step,
        generate_fact_image_step,
        generate_fun_fact_typing,
        generate_fun_fact_canvas,
        add_background_music_step,
        export_final_fun_fact,
        extract_final_frame,
        upload_final_video,
    ],
    write_debug=True,
)

# Execução real
pipeline_fun_fact.execute({"country_name": "Australia", "fact_number": "1"})
