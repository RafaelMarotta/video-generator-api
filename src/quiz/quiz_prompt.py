import json
import re
from core.commons.openai import llm
from core.domain.pipeline import Step
from typing import Callable

def sanitize_output(output: str) -> str:
  output = output.strip()

  # Remove aspas ao redor se a string toda estiver entre aspas simples ou duplas
  if (output.startswith("'") and output.endswith("'")) or (output.startswith('"') and output.endswith('"')):
    output = output[1:-1]

  # Remove blocos markdown (```json ... ```)
  output = re.sub(r"^```(?:json)?", "", output, flags=re.IGNORECASE)
  output = re.sub(r"```$", "", output)

  # Corrige aspas curvas que o modelo às vezes coloca
  output = output.replace("“", "\"").replace("”", "\"").replace("’", "'")

  # Remove \n desnecessários mas mantém conteúdo UTF-8
  return output.strip()

class GenerateQuizInputStep(Step):
  def __init__(
    self,
    name: str,
    description: str,
    input_transformer: Callable[[dict], dict] = None,
  ):
    super().__init__(name, description, input_transformer)

  def execute(self, input: dict, context: dict):
    topic = input["text"]
    question_number = input.get("number", "1")

    system_prompt = (
      "You are a creative assistant responsible for generating fun and engaging quiz content for short interactive videos.\n\n"
      "Given a topic, your task is to create a JSON input for the video pipeline using the following structure:\n\n"
      "- question: a single quiz question in Portuguese, written in a fun and challenging tone, like you're daring a friend. (Max 96 chars)\n"
      "- answers: a list containing exactly 4 answer options, each as a dictionary with:\n"
      "    - text: the answer text (max: 30 chars)\n"
      "    - correct: a boolean indicating whether it is the correct answer\n\n"
      "Important guidelines:\n"
      "- The question must NOT be a yes/no question and should ask only ONE thing at a time\n"
      "- Only ONE of the answers must be marked as correct (\"correct\": true)\n"
      "- The quiz must be surprising, interesting or amusing — avoid technical, factual or obvious questions\n"
      "- Keep the question concise, direct, and engaging — avoid long or compound sentences\n"
      "- Output ONLY the pure JSON object, parsable as valid Python code using ast.literal_eval\n"
      "- Do NOT include explanations, comments, Markdown formatting, or any text before or after\n"
      "- Do NOT wrap the output in triple backticks or quotation marks\n"
    )

    user_input = f"Topic: {topic}\nQuestion Number: {question_number}"

    def validate_response(output: str) -> bool:
      try:
        print("RAW OUTPUT FROM LLM:", repr(output))
        sanitized = sanitize_output(output)
        parsed = json.loads(sanitized)
        if not isinstance(parsed, dict):
          return False

        if "question" not in parsed or "answers" not in parsed:
          return False

        answers = parsed["answers"]
        if not isinstance(answers, list) or len(answers) != 4:
          return False

        correct_count = sum(
          1 for a in answers if isinstance(a, dict) and a.get("correct") is True
        )
        return correct_count == 1 and all("text" in a and "correct" in a for a in answers)
      except Exception as e:
        print("VALIDATION ERROR:", str(e))
        return False

    raw_output = llm(
      system_prompt=system_prompt,
      user_input=user_input,
      validate_response=validate_response,
      max_retries=1,
    )

    if isinstance(raw_output, dict) and "error" in raw_output:
      print(raw_output["error"])
      raise ValueError(f"Failed to generate quiz input: {raw_output['error']}")

    try:
      parsed_output = json.loads(sanitize_output(raw_output))
    except Exception as e:
      raise ValueError(f"Could not parse quiz output: {e}")

    context[self.name] = parsed_output
