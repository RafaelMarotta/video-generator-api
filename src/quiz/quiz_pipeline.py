from quiz_canvas import GenerateQuestionCanvas, GenerateAnswerCanvas
from core.domain.pipeline import Pipeline, ForeachStep
from core.domain.video import ExportVideo, ConcatenateVideoStep
from core.domain.debug import ExtractFrameStep
from core.domain.caption import (
    GenerateCaptionStepWithSpeech,
    GenerateCaptionWithSpeechInput,
    BackgroundConfig,
)

font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"

generate_question_typing = GenerateCaptionStepWithSpeech(
    "generate_question_typing",
    "Gera a legenda animada e a narração da pergunta do quiz",
    lambda context: GenerateCaptionWithSpeechInput(
        text=context["question_text"],
        effect="typing",
        max_lines=4,
        max_chars_per_line=25,
        font_size=70,
        font_path=font_path,
        color="black",
        background=BackgroundConfig(color=(255, 255, 255), padding=40, width=800),
    ),
)

generate_question_canvas = GenerateQuestionCanvas(
    "generate_question_canvas",
    "Monta o visual da pergunta com o background, legenda e áudio",
    lambda context: {
        "background_path": "src/quiz/assets/background-quiz.png",
        "typing_clip": context["generate_question_typing"]["typing_clip"],
        "audio_clip": context["generate_question_typing"]["audio_clip"],
    },
)

answers_pipeline = Pipeline(
    "answers_pipeline",
    "Pipeline de geração de vídeos com alternativas do quiz",
    [
        GenerateCaptionStepWithSpeech(
            f"generate_answer_typing",
            f"Gera a legenda animada e a narração da alternativa",
            lambda context: GenerateCaptionWithSpeechInput(
                text=context["current"],
                max_lines=2,
                max_chars_per_line=25,
                font_size=70,
                font_path=font_path,
                color="black",
                background=BackgroundConfig(
                    color=(255, 255, 255), padding=40, width=800
                ),
            ),
        ),
        GenerateAnswerCanvas(
            "generate_answer_canvas",
            "Composição visual da alternativa",
            lambda context: {
                "last_frame": context["last_canvas"]["last_frame"],
                "top_margin": context["last_canvas"]["top_margin"],
                "typing_clip": context["generate_answer_typing"]["typing_clip"],
                "audio_clip": context["generate_answer_typing"]["audio_clip"],
            },
        ),
    ],
)

create_answers = ForeachStep(
    "create_answers",
    "Geração de vídeos com alternativas do quiz",
    lambda context: {"items": context["answers"]},
    answers_pipeline,
)

join_video = ConcatenateVideoStep(
    "join_video",
    "Concatena todos os vídeos da pergunta e alternativas em sequência",
)

extract_final_frame = ExtractFrameStep(
    "extract_final_frame",
    "Extração do último frame do vídeo final",
    lambda context: {"final_video": context["join_video"]["final_video"]},
)

final_step = ExportVideo(
    "export_video",
    "Exporta o vídeo final para um arquivo MP4",
    lambda context: {
        "final_video": context["join_video"]["final_video"],
    },
)

pipeline = Pipeline(
    "pipeline_quiz_animado",
    "Pipeline de geração de vídeo animado com pergunta e 4 alternativas",
    [
        generate_question_typing,
        generate_question_canvas,
        create_answers,
        join_video,
        final_step,
        #extract_final_frame,
    ],
)

pipeline.execute(
    {
        "question_text": "Qual desses animais é capaz de dormir com metade do cérebro acordado?",
        "answers": ["A) Golfinho", "B) Gato", "C) Coruja", "D) Tubarão"],
    }
)
