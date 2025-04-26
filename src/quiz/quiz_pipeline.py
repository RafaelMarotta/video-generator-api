from quiz_canvas import GenerateQuestionCanvas, GenerateAnswerCanvas
from core.domain.pipeline import Pipeline
from core.domain.video import ExportVideo, ConcatenateVideoStep
from core.domain.caption import (
    GenerateCaptionStepWithSpeech,
    GenerateCaptionWithSpeechInput,
    BackgroundConfig
)

# Step 1: Geração da legenda animada e narração da pergunta
generate_question_typing = GenerateCaptionStepWithSpeech(
    "generate_question_typing",
    "Gera a legenda animada e a narração da pergunta do quiz",
    lambda context: GenerateCaptionWithSpeechInput(
        text="Qual desses animais é capaz de dormir com metade do cérebro acordado?",
        effect="typing",
        max_lines=4,
        max_chars_per_line=25,
        font_size=70,
        font_path="/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        color="black",
        background=BackgroundConfig(color=(255, 255, 255), padding=40, width=800),
    ),
)

# Step 2: Composição visual do enunciado
generate_question_canvas = GenerateQuestionCanvas(
    "generate_question_canvas",
    "Monta o visual da pergunta com o background, legenda e áudio",
    lambda context: {
        "background_path": "src/quiz/assets/background-quiz.png",
        "typing_clip": context["generate_question_typing"]["typing_clip"],
        "audio_clip": context["generate_question_typing"]["audio_clip"],
    },
)

# Step 3 a 6: Geração das alternativas e composição de cada uma
alternatives = [
    "A) Golfinho",
    "B) Gato",
    "C) Coruja",
    "D) Tubarão"
]

steps = []
previous_canvas_key = "generate_question_canvas"

for i, alt_text in enumerate(alternatives, start=1):
    typing_step = GenerateCaptionStepWithSpeech(
        f"generate_answer_typing{i}",
        f"Gera a legenda animada e a narração da alternativa {alt_text}",
        lambda context, alt_text=alt_text: GenerateCaptionWithSpeechInput(
            text=alt_text,
            max_lines=2,
            max_chars_per_line=25,
            font_size=70,
            font_path="/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            color="black",
            background=BackgroundConfig(color=(255, 255, 255), padding=40, width=800),
        ),
    )
    canvas_step = GenerateAnswerCanvas(
        f"generate_answer_canvas{i}",
        f"Composição visual da alternativa {alt_text}",
        lambda context, typing_key=typing_step.name, prev_canvas=previous_canvas_key: {
            "last_frame": context[prev_canvas]["last_frame"],
            "top_margin": context[prev_canvas]["top_margin"],
            "typing_clip": context[typing_key]["typing_clip"],
            "audio_clip": context[typing_key]["audio_clip"],
        },
    )
    steps.extend([typing_step, canvas_step])
    previous_canvas_key = canvas_step.name

# Step 7: Junta os vídeos das perguntas e alternativas
join_video = ConcatenateVideoStep(
    "join_video",
    "Concatena todos os vídeos da pergunta e alternativas em sequência",
    lambda context: {
        "video_clips": [
            context["generate_question_canvas"]["composite"],
            context["generate_answer_canvas1"]["composite"],
            context["generate_answer_canvas2"]["composite"],
            context["generate_answer_canvas3"]["composite"],
            context["generate_answer_canvas4"]["composite"],
        ]
    },
)

# Step 8: Exporta o vídeo final
final_step = ExportVideo(
    "export_video",
    "Exporta o vídeo final para um arquivo MP4",
    lambda context: {
        "final_video": context["join_video"]["final_video"],
    },
)

# Montagem da pipeline
pipeline = Pipeline(
    "pipeline_quiz_animado",
    "Pipeline de geração de vídeo animado com pergunta e 4 alternativas",
    [
        generate_question_typing,
        generate_question_canvas,
        *steps,
        join_video,
        final_step,
    ],
)

pipeline.execute({})
