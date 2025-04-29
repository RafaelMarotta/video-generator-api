from core.domain.pipeline import Step
from core.commons.openai import generate_image_from_text, download_image_from_url
from typing import Callable

class GenerateImageStep(Step):
    def __init__(self, name: str, description: str, input_transformer: Callable[[dict], dict] = None):
        super().__init__(name, description, input_transformer)

    def execute(self, input: dict, context: dict):
        print(input)
        prompt = input["prompt"]
        output_key = input.get("output_key", "generated_image_path")
        size = input.get("size", "1024x1024")
        use_tempfile = input.get("use_tempfile", False)

        # 1. Generate the image(s)
        image_urls = generate_image_from_text(prompt, n=1, size=size)
        if not image_urls:
            raise ValueError("Failed to generate image from prompt.")

        # 2. Download the first image
        local_image_path = download_image_from_url(image_urls[0], use_tempfile=use_tempfile)

        # 3. Save the result in the context
        context[self.name] = {
            output_key: local_image_path
        }
