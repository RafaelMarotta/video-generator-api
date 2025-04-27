from countries_fun_facts.fun_facts_canvas import GenerateFunFactCanvas
from core.domain.caption import (
    GenerateCaptionStepWithSpeech,
    GenerateCaptionWithSpeechInput,
)
from core.domain.caption_ai import GenerateCaptionAIStep
from core.domain.video import ExportVideo
from core.domain.debug import ExtractFrameStep
from core.domain.pipeline import Pipeline

font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"

generate_fun_fact_typing = GenerateCaptionAIStep(
    "generate_fun_fact_typing",
    "Gera a legenda animada e a narração da curiosidade",
    lambda context: GenerateCaptionWithSpeechInput(
        text=context["fun_fact_text"],
        max_lines=3,
        max_chars_per_line=35,
        font_size=50,
        width=800,
        height=250,
        font_path=font_path,
        color="white",
    ),
)

generate_fun_fact_canvas = GenerateFunFactCanvas(
    "generate_fun_fact_canvas",
    "Composição visual da curiosidade com imagem e legenda",
    lambda context: {
        "title_text": context["title_text"],
        "font_path": font_path,
        "fact_number": context["fact_number"],
        "background_path": "src/countries_fun_facts/assets/background-fun-facts.png",
        "typing_clip": context["generate_fun_fact_typing"]["typing_clip"],
        "audio_clip": context["generate_fun_fact_typing"]["audio_clip"],
        "fact_image": context["fact_image"],
        "country_code": context["country_code"],
    },
)

export_final_fun_fact = ExportVideo(
    "export_final_fun_fact",
    "Exporta o vídeo de curiosidade para um arquivo MP4",
    lambda context: {"final_video": context["composites"][0]},
)

extract_final_frame = ExtractFrameStep(
    "extract_final_frame",
    "Extração do último frame do vídeo final",
    lambda context: {
        "final_video": context["composites"][0]
    },
)

pipeline_fun_fact = Pipeline(
    "pipeline_fun_fact_country",
    "Pipeline de geração de vídeo com curiosidade sobre um país",
    [
        generate_fun_fact_typing,
        generate_fun_fact_canvas,
        export_final_fun_fact,
        # extract_final_frame,
    ],
)

# Execução da pipeline
pipeline_fun_fact.execute({
    "title_text": "Curiosidades sobre o Brasil",
    "fact_image": "src/countries_fun_facts/assets/example.png",
    "country_code": "br",
    "fun_fact_text": "Na cidade de Belém, existe um mercado chamado Ver-o-Peso onde você encontra desde ervas medicinais da floresta até poções do amor vendidas por feiticeiras locais. É um dos mercados mais antigos e místicos da América Latina!",
    "fact_number": "1"
})
