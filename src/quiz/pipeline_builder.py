# src/quiz/pipeline_builder.py

import os
from core.domain.caption_ai import GenerateCaptionAIStep
from core.domain.pipeline import Pipeline, ForeachStep
from core.domain.caption import (
    GenerateCaptionStepWithSpeech,
    GenerateCaptionWithSpeechInput,
    BackgroundConfig,
)
from core.domain.video import AddBackgroundMusicStep, ConcatenateVideoStep, ExportVideo
from core.domain.debug import ExtractFrameStep
from core.domain.progress_bar import GenerateProgressBarStep
from quiz.quiz_prompt import GenerateQuizInputStep
from quiz.quiz_canvas import (
    GenerateQuestionCanvas,
    GenerateAnswerCanvas,
    GenerateProgressBarCanvas,
)

font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "")


def build_pipeline_quiz() -> Pipeline:
    return Pipeline(
        "pipeline_quiz_animado",
        "Pipeline de geração de vídeo animado com pergunta e 4 alternativas. Forneça o tema do quiz:",
        steps=[
            GenerateQuizInputStep(
                "input_step",
                "Gera o roteiro completo do quiz",
                lambda context: {
                    "text": context["text"],
                    "number": context["number"],
                },
            ),
            GenerateCaptionAIStep(
                "generate_question_typing",
                "Gera a legenda animada e a narração da pergunta do quiz",
                lambda context: GenerateCaptionWithSpeechInput(
                    text=context["input_step"]["question"],
                    max_lines=4,
                    max_chars_per_line=32,
                    font_size=55,
                    font_path=font_path,
                    width=800,
                    height=380,
                    stroke_color="white",
                    color="black",
                    background=BackgroundConfig(
                        color=(255, 255, 255), padding=40, width=800
                    ),
                ),
            ),
            GenerateQuestionCanvas(
                "generate_question_canvas",
                "Monta o visual da pergunta com o background, legenda e áudio",
                lambda context: {
                    "background_path": "src/quiz/assets/background-quiz.png",
                    "typing_clip": context["generate_question_typing"]["typing_clip"],
                    "audio_clip": context["generate_question_typing"]["audio_clip"],
                },
            ),
            ForeachStep(
                "create_answers",
                "Geração de vídeos com alternativas do quiz",
                lambda context: {"items": context["input_step"]["answers"]},
                Pipeline(
                    "answers_pipeline",
                    "Pipeline de geração de vídeos com alternativas do quiz",
                    [
                        GenerateCaptionAIStep(
                            "generate_answer_typing",
                            "Gera a legenda animada e a narração da alternativa",
                            lambda context: GenerateCaptionWithSpeechInput(
                                text=context["current"]["text"],
                                max_lines=2,
                                max_chars_per_line=25,
                                width=800,
                                height=120,
                                font_size=55,  # ligeiramente maior
                                font_path=font_path,
                                stroke_color="white",
                                color="black",
                                background=BackgroundConfig(
                                    color=(255, 255, 255)  # apenas a cor do fundo agora
                                    # opacity pode ser adicionado se quiser controlar transparência
                                ),
                            ),
                        ),
                        GenerateAnswerCanvas(
                            "generate_answer_canvas",
                            "Composição visual da alternativa",
                            lambda context: {
                                "last_frame": context["last_canvas"]["last_frame"],
                                "top_margin": context["last_canvas"]["top_margin"],
                                "typing_clip": context["generate_answer_typing"][
                                    "typing_clip"
                                ],
                                "audio_clip": context["generate_answer_typing"][
                                    "audio_clip"
                                ],
                            },
                        ),
                    ],
                ),
            ),
            GenerateProgressBarStep(
                "progress_bar",
                "Geração da barra de progresso do quiz",
            ),
            GenerateProgressBarCanvas(
                "progress_bar_canvas",
                "Renderiza visualmente a barra de progresso",
                lambda context: {
                    "progress_clip": context["progress_bar"]["progress_clip"],
                    "last_frame": context["last_canvas"]["last_frame"],
                },
            ),
            ConcatenateVideoStep(
                "join_video",
                "Concatena todos os vídeos da pergunta e alternativas em sequência",
            ),
             AddBackgroundMusicStep(
                "add_background_music_step",
                "Adiciona música de fundo ao vídeo",
                lambda context: {
                    "final_video": context["join_video"]["final_video"],
                    "background_music_path": "src/countries_fun_facts/assets/background.mp3",
                },
            ),
            ExportVideo(
              "export_video",
              "Exporta o vídeo final para um arquivo MP4",
              lambda context: {
                "final_video": context["add_background_music_step"]["final_video"],
                "output_path": os.path.join(OUTPUT_PATH, context["id"] + ".mp4"),
              },
            ),
            # ExtractFrameStep(
            #     "extract_final_frame",
            #     "Extrai o último frame do vídeo final",
            #     lambda context: {"final_video": context["join_video"]["final_video"], "time_in_seconds": 8},
            # ),
        ],
        write_debug=True,
    )
