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
  output = output.replace(""", "\"").replace(""", "\"").replace("'", "'")

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
    num_questions = context.get("n", 3)
    tone_prompt = context.get("tone_prompt", "")
    
    try:
        num_questions = int(num_questions)
    except ValueError:
        num_questions = 3
    
    system_prompt = (
        # Define a personalidade/tom com mais ênfase
        f"{tone_prompt}\n\n"
        "You MUST maintain this exact personality and tone throughout ALL your responses. This means:\n"
        "- Use vocabulary and expressions that match your personality\n"
        "- Keep the same speaking style in both questions and answers\n"
        "- Adapt your writing to reflect your character's unique way of thinking\n"
        "- Be consistent with your tone's level of formality or casualness\n\n"
        
        f"As this character, you are creating a quiz for a video. Your questions and answers should feel like they're being asked by this specific personality.\n\n"
        
        f"Given a topic, create a JSON input for the video pipeline containing a list of {num_questions} questions using the following structure:\n\n"
        "{\n"
        "  \"questions\": [\n"
        "    {\n"
        "      \"question\": \"a quiz question in Portuguese (Max 96 chars)\",\n"
        "      \"answers\": [\n"
        "        {\"text\": \"answer text (max 30 chars)\", \"correct\": boolean},\n"
        "        ... (4 answers total)\n"
        "      ]\n"
        "    },\n"
        f"    ... ({num_questions} questions total)\n"
        "  ]\n"
        "}\n\n"
        "Important guidelines:\n"
        f"- Generate EXACTLY {num_questions} different questions about the topic\n"
        "- Questions must NOT be yes/no questions and should ask only ONE thing at a time\n"
        "- Each question must have EXACTLY 4 answers with only ONE correct answer\n"
        "- The quiz must be surprising, interesting or amusing — avoid obvious questions\n"
        "- Keep questions concise, direct, and engaging — avoid long or compound sentences\n"
        "- Output ONLY the pure JSON object, parsable as valid Python code\n"
        "- Do NOT include explanations, comments, Markdown formatting, or any text before or after\n\n"
        
        "CRITICAL TONE GUIDELINES:\n"
        "- If you're a professor: use educational language and interesting facts in your wrong answers\n"
        "- If you're funny: include humor in both questions and wrong answers, but keep correct answers clear\n"
        "- If you're sarcastic: use clever wordplay and irony, especially in the wrong answers\n"
        "- If you're enthusiastic: use dynamic language and exciting phrasings\n"
        "- If you're casual: write like you're chatting with friends, but keep it clear\n"
        "- ALWAYS maintain your personality's way of speaking in BOTH questions and answers\n"
        "- Make wrong answers match the tone while still being clearly incorrect\n"
        "- Your personality should be immediately recognizable in how you phrase things\n"
    )

    print("SYSTEM PROMPT:", system_prompt)

    user_input = f"Topic: {topic}\nNumber of Questions: {num_questions}"

    def validate_response(output: str) -> bool:
        try:
            print("RAW OUTPUT FROM LLM:", repr(output))
            sanitized = sanitize_output(output)
            parsed = json.loads(sanitized)
            
            # Verifica se é um dicionário e tem a chave "questions"
            if not isinstance(parsed, dict) or "questions" not in parsed:
                print("ERROR: Output must be a dict with 'questions' key")
                return False

            questions = parsed["questions"]
            
            # Verifica se questions é uma lista com exatamente o número especificado de questões
            if not isinstance(questions, list) or len(questions) != num_questions:
                print(f"ERROR: Must have exactly {num_questions} questions")
                return False

            # Valida cada questão
            for i, question in enumerate(questions):
                # Verifica se tem as chaves necessárias
                if not isinstance(question, dict) or "question" not in question or "answers" not in question:
                    print(f"ERROR: Question {i} missing required fields")
                    return False

                answers = question["answers"]
                if not isinstance(answers, list) or len(answers) != 4:
                    print(f"ERROR: Question {i} must have exactly 4 answers")
                    return False

                # Verifica se tem exatamente uma resposta correta
                correct_count = sum(1 for a in answers if isinstance(a, dict) and a.get("correct") is True)
                if correct_count != 1:
                    print(f"ERROR: Question {i} must have exactly 1 correct answer")
                    return False

                # Verifica se todas as respostas têm os campos necessários
                for j, answer in enumerate(answers):
                    if not isinstance(answer, dict) or "text" not in answer or "correct" not in answer:
                        print(f"ERROR: Answer {j} in question {i} missing required fields")
                        return False

            return True
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
        print("DEBUG - Parsed Output Structure:", json.dumps(parsed_output, indent=2))
        context[self.name] = parsed_output
        return parsed_output
    except Exception as e:
        raise ValueError(f"Could not parse quiz output: {e}")
