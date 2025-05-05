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

        system_prompt = (
            "You are a creative assistant responsible for helping generate captivating short videos about fun facts related to different countries.\n\n"
            "Given the name of a country, your task is to create a JSON input for the video pipeline, using the following structure:\n\n"
            "{\n"
            '  "title_text": "Curiosidades sobre o [Country Name] #[Number]",\n'
            '  "fact_image_prompt": "[A detailed and realistic photo-style image prompt that represents the fun fact, without text, borders, logos, or frame.]",\n'
            '  "country_code": "[2-letter ISO country code]",\n'
            '  "fun_fact_text": "[A truly surprising, intriguing, or culturally rich fun fact about the country, written in Portuguese, using an engaging, storytelling tone. It should sound natural and interesting as if it were narrated to keep the viewer curious.]",\n'
            '  "number": "[The fact number as a string]"\n'
            "}\n\n"
            "Important guidelines:\n"
            "- Prioritize surprising, little-known, or very interesting facts instead of generic or obvious information.\n"
            "- The fun fact text must be written in Portuguese with a casual and fluent tone, as if narrating a short story or telling a surprising curiosity to a friend.\n"
            "- Make the storytelling vivid, sometimes using expressions that capture attention like 'Você sabia que...', 'Incrivelmente...', 'Pouca gente conhece...'.\n"
            "- The image prompt must describe an iconic, scenic, or culturally symbolic place related to the fact, in realistic photographic style.\n"
            "- Do not include any branding, watermarks, borders, logos, or visual UI elements in the image prompt.\n"
            "- Output ONLY the pure JSON object, parsable as valid Python code.\n"
            "- Do NOT include any explanations, comments, or wrap the JSON in triple backticks."
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
