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
        num_facts = context.get("n", 1)  # Get number of facts from context, default to 3
        tone_prompt = context.get("tone_prompt", "")  # Get tone_prompt from context

        try:
            num_facts = int(num_facts)
        except ValueError:
            num_facts = 1

        system_prompt = (
            # Define a personalidade/tom
            f"{tone_prompt}\n\n"
            "With this personality and tone in mind, you are a creative assistant responsible for helping generate captivating short videos about fun facts related to different countries.\n\n"
            "Given a topic (which can be a country, city, event, cultural activity, or any subject), your task is to create a JSON input for the video pipeline containing a list of fun facts, using the following structure:\n\n"
            "{\n"
            '  "facts": [\n'
            '    {\n'
            '      "title_text": "Curiosidades sobre [Topic] #[Number]",\n'
            '      "fact_image_prompt": "[A detailed and realistic photo-style image prompt that represents the fun fact, without text, borders, logos, or frame.]",\n'
            '      "country_code": "[2-letter ISO country code of the country most associated with this topic]",\n'
            '      "fun_fact_text": "[A truly surprising, intriguing, or culturally rich fun fact about the topic, written in Portuguese, using your defined tone and personality.]",\n'
            '      "number": "[The fact number as a string]"\n'
            '    },\n'
            f'    ... ({num_facts} facts total)\n'
            '  ]\n'
            "}\n\n"
            "Important guidelines:\n"
            "- Generate EXACTLY the specified number of different facts about the topic\n"
            "- Each fact should be unique and not overlap with others\n"
            "- Prioritize surprising, little-known, or very interesting facts instead of generic information\n"
            "- The fun fact text must be written in Portuguese maintaining your specific tone and personality\n"
            "- Adapt your storytelling style based on your tone:\n"
            "  * If funny: Use playful language and humorous observations\n"
            "  * If serious: Focus on precise and informative descriptions\n"
            "  * If enthusiastic: Show genuine excitement about the facts\n"
            "- The image prompt must describe an iconic, scenic, or culturally symbolic place related to the fact\n"
            "- Do not include any branding, watermarks, borders, logos, or visual UI elements in the image prompt\n"
            "- Output ONLY the pure JSON object, parsable as valid Python code\n"
            "- Do NOT include any explanations, comments, or wrap the JSON in triple backticks\n"
            "- IMPORTANT: Maintain your personality's way of speaking throughout the text\n"
            "- Your tone should be immediately recognizable in how you present the facts\n\n"
            "CRITICAL COUNTRY CODE REQUIREMENTS:\n"
            "- You MUST always return a valid 2-letter ISO country code in the 'country_code' field\n"
            "- For any topic (event, activity, or subject), determine which country it is most associated with\n"
            "- Examples of topic-to-country mapping:\n"
            "  * 'Baile em Assunção' → 'PY' (Paraguay)\n"
            "  * 'Carnaval do Rio' → 'BR' (Brazil)\n"
            "  * 'Festa de São João' → 'PT' (Portugal)\n"
            "  * 'Festa do Bumba Meu Boi' → 'BR' (Brazil)\n"
            "- The country code must be a valid ISO 3166-1 alpha-2 code\n"
            "- Do not leave the country_code field empty or use placeholder values\n"
            "- The country code is essential for displaying the correct flag in the video"
        )

        user_input = f"Topic: {country_name}\nNumber of Facts: {num_facts}"

        def validate_response(output: str) -> bool:
            try:
                parsed = ast.literal_eval(output)
                if not isinstance(parsed, dict) or "facts" not in parsed:
                    print("ERROR: Output must be a dict with 'facts' key")
                    return False

                facts = parsed["facts"]
                if not isinstance(facts, list) or len(facts) != num_facts:
                    print(f"ERROR: Must have exactly {num_facts} facts")
                    return False

                required_keys = {
                    "title_text",
                    "fact_image_prompt",
                    "country_code",
                    "fun_fact_text",
                    "number",
                }

                for i, fact in enumerate(facts):
                    if not isinstance(fact, dict) or not required_keys.issubset(fact.keys()):
                        print(f"ERROR: Fact {i} missing required fields")
                        return False
                    
                    # Validate country code
                    country_code = fact.get("country_code", "")
                    if not isinstance(country_code, str) or len(country_code) != 2:
                        print(f"ERROR: Fact {i} has invalid country code: {country_code}")
                        return False

                return True
            except Exception as e:
                print("VALIDATION ERROR:", str(e))
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
        return parsed_output
