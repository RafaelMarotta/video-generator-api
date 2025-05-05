# test_quiz_pipeline.py

from quiz.pipeline_builder import build_pipeline_quiz

if __name__ == "__main__":
    pipeline = build_pipeline_quiz()

    # Parâmetros de entrada simulados
    input_data = {
        "id": "quiz-test-0001",
        "text": "Futebol",
        "number": "1"
    }

    print("🔄 Iniciando execução da pipeline do quiz...")
    context = pipeline.run(input_data)
    print("✅ Pipeline finalizada com sucesso!")

    output_path = context["export_video"]["output_path"]
    print(f"📽️ Vídeo exportado em: {output_path}")
