# src/quiz/pipeline_builder.py

import os
from core.domain.pipeline import Pipeline, ForeachStep, Step
from core.domain.caption_ai import (
    GenerateCaptionStep,
    GenerateCaptionWithSpeechStep,
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
    GenerateCorrectAnswerCanvas
)
from dataclasses import dataclass

font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
OUTPUT_PATH = os.getenv("OUTPUT_PATH", "")

# Adicionando uma nova classe de Step concreta
class StoreCurrentQuestionStep(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        context[self.name] = input
        return input

# Adicione esta nova classe no início do arquivo junto com as outras classes
class ClearAnswersContextStep(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        # Limpa o contexto das respostas anteriores
        if "create_answers" in context:
            context["create_answers"] = {}
        return input

def build_pipeline_quiz() -> Pipeline:
    return Pipeline(
        "pipeline_quiz_animado",
        "Pipeline de geração de vídeos animados com perguntas e respostas. Forneça o tema do quiz:",
        steps=[
            GenerateQuizInputStep(
                "input_step",
                "Gera o roteiro completo do quiz",
                lambda context: {
                    "text": context["text"],
                },
            ),
            ForeachStep(
                "create_questions",
                "Geração de vídeos para cada questão do quiz",
                lambda context: {"items": context["input_step"]["questions"]},
                Pipeline(
                    "question_pipeline",
                    "Pipeline de geração de vídeo para cada questão",
                    [
                        # Adiciona o step de limpeza no início
                        ClearAnswersContextStep(
                            "clear_answers_context",
                            "Limpa o contexto das respostas anteriores",
                        ),
                        StoreCurrentQuestionStep(
                            "store_current_question",
                            "Armazena a questão atual para uso posterior",
                            lambda context: {
                                "current_question": context["current"]
                            }
                        ),
                        GenerateCaptionWithSpeechStep(
                            "generate_question_typing",
                            "Gera a legenda animada e a narração da pergunta do quiz",
                            lambda context: GenerateCaptionWithSpeechInput(
                                text=context["current"]["question"],
                                max_lines=4,
                                max_chars_per_line=32,
                                font_size=55,
                                font_path=font_path,
                                width=800,
                                height=380,
                                stroke_color="white",
                                color="black",
                                text_align="center",
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
                            lambda context: {"items": context["current"]["answers"]},
                            Pipeline(
                                "answers_pipeline",
                                "Pipeline de geração de vídeos com alternativas do quiz",
                                [
                                    GenerateCaptionWithSpeechStep(
                                        "generate_answer_typing",
                                        "Gera a legenda animada e a narração da alternativa",
                                        lambda context: GenerateCaptionWithSpeechInput(
                                            text=context["current"]["text"],
                                            max_lines=2,
                                            max_chars_per_line=25,
                                            width=800,
                                            height=120,
                                            font_size=55,
                                            font_path=font_path,
                                            stroke_color="white",
                                            color="black",
                                            text_align="center",
                                            background=BackgroundConfig(
                                                color=(255, 255, 255)
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
                        GenerateCaptionStep(
                            "generate_correct_answer_typing",
                            "Gera a legenda animada da resposta correta",
                            lambda context: GenerateCaptionWithSpeechInput(
                                text=next((a["text"] for a in context["store_current_question"]["current_question"]["answers"] if a.get("correct")), "Resposta correta não encontrada"),
                                max_lines=2,
                                max_chars_per_line=25,
                                width=800,
                                height=120,
                                font_size=55,
                                font_path=font_path,
                                full_duration=3,
                                stroke_color="black",
                                color="white",
                                text_align="center",
                                background=BackgroundConfig(
                                    color=(27, 128, 37)
                                ),
                            ),
                        ),
                        GenerateCorrectAnswerCanvas(
                            "generate_correct_answer_canvas",
                            "Gera o canvas da resposta correta",
                            lambda context: {
                                "question_typing": context["generate_question_typing"]["typing_clip"],
                                "answers_clips": context["create_answers"].get("typings", []),
                                "typing_clip": context["generate_correct_answer_typing"]["typing_clip"],
                                "correct_answer_idx": next((i for i, answer in enumerate(context["store_current_question"]["current_question"]["answers"]) if answer.get("correct")), 0),
                                "background_path": "src/quiz/assets/background-quiz.png"
                            }
                        ),
                    ],
                ),
            ),
            ConcatenateVideoStep(
                "join_video",
                "Concatena todos os vídeos das questões em sequência",
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
        ],
        write_debug=True,
    )
