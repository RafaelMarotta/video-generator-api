import os
from openai import OpenAI
import logging
from typing import Callable, Any

logging.basicConfig(level=logging.ERROR)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm(
    system_prompt: str,
    user_input: str,
    validate_response: Callable[[Any], bool],
    expected_output: str = None,
    max_retries: int = 3
) -> Any:

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]

    if expected_output:
        messages.append({"role": "user", "content": f"Expected Output: {expected_output}"})

    attempt = 0

    while attempt < max_retries:
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            content = response.model_dump()["choices"][0]["message"]["content"]

            if validate_response(content):
                return content
            else:
                logging.warning(f"Validation failed on attempt {attempt + 1}. Retrying...")
        
        except Exception as e:
            logging.error(f"Error communicating with OpenAI API: {e}")
            return {"error": str(e)}

        attempt += 1

    logging.error("Max retries reached. LLM output is invalid.")
    return {"error": "Max retries reached. Invalid LLM output."}

# def generateImage(input_text):
#     try:
#         response = openai.Image.create(
#             prompt=input_text,
#             n=1,
#             size="1024x1024"
#         )
#         image_url = response['data'][0]['url']
#         return {"image_url": image_url}
#     except Exception as e:
#         return {"error": str(e)}
