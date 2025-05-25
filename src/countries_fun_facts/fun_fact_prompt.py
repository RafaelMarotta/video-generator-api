import ast
from core.commons.openai import llm  # Your generic LLM function
from core.domain.pipeline import Step
from typing import Callable


class GenerateFunFactInputStep(Step):
    def __init__(
        self,
        name: str,
        description: str,
        input_transformer: Callable[[dict], dict] = None,
    ):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        country_name = input["country_name"]
        number = input.get("number", "1")
        tone_prompt = context.get("tone_prompt", "")  # Get tone_prompt from context

        system_prompt = (
            # Define a personalidade/tom
            f"{tone_prompt}\n\n"
            "With this personality and tone in mind, you are a creative assistant responsible for helping generate captivating short videos about fun facts related to different countries.\n\n"
            "Given the name of a country, your task is to create a JSON input for the video pipeline, using the following structure:\n\n"
            "{\n"
            '  "title_text": "Curiosidades sobre o [Country Name] #[Number]",\n'
            '  "fact_image_prompt": "[A detailed and realistic photo-style image prompt that represents the fun fact, without text, borders, logos, or frame.]",\n'
            '  "country_code": "[2-letter ISO country code]",\n'
            '  "fun_fact_text": "[A truly surprising, intriguing, or culturally rich fun fact about the country, written in Portuguese, using your defined tone and personality.]",\n'
            '  "number": "[The fact number as a string]"\n'
            "}\n\n"
            "Important guidelines:\n"
            "- Prioritize surprising, little-known, or very interesting facts instead of generic information.\n"
            "- The fun fact text must be written in Portuguese maintaining your specific tone and personality.\n"
            "- Adapt your storytelling style based on your tone:\n"
            "  * If funny: Use playful language and humorous observations\n"
            "  * If serious: Focus on precise and informative descriptions\n"
            "  * If enthusiastic: Show genuine excitement about the facts\n"
            "- The image prompt must describe an iconic, scenic, or culturally symbolic place related to the fact.\n"
            "- Do not include any branding, watermarks, borders, logos, or visual UI elements in the image prompt.\n"
            "- Output ONLY the pure JSON object, parsable as valid Python code.\n"
            "- Do NOT include any explanations, comments, or wrap the JSON in triple backticks.\n"
            "- IMPORTANT: Maintain your personality's way of speaking throughout the text.\n"
            "- Your tone should be immediately recognizable in how you present the facts."
        )

        user_input = f"Country: {country_name}\nFact Number: {number}"

        def validate_response(output: str) -> bool:
            try:
                parsed = ast.literal_eval(output)
                required_keys = {
                    "title_text",
                    "fact_image_prompt",
                    "country_code",
                    "fun_fact_text",
                    "number",
                }
                return isinstance(parsed, dict) and required_keys.issubset(
                    parsed.keys()
                )
            except Exception:
                return False

        raw_output = llm(
            system_prompt=system_prompt,
            user_input=user_input,
            validate_response=validate_response,
            max_retries=3,
        )

        if isinstance(raw_output, dict) and "error" in raw_output:
            raise ValueError(
                f"Failed to generate fun fact input: {raw_output['error']}"
            )

        parsed_output = ast.literal_eval(raw_output)

        context[self.name] = parsed_output
