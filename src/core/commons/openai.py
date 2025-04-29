import os
from openai import OpenAI
import logging
import openai
from typing import Callable, Any, List
import requests
import tempfile
from PIL import Image

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
                model="gpt-4.1",
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


def generate_image_from_text(input_text: str, n: int = 1, size: str = "1024x1024") -> list:
    """
    Generate image(s) from a text prompt using OpenAI's DALL·E 3 API.
    Args:
        input_text (str): The text prompt to generate the image from.
        n (int): Number of images to generate. Default is 1.
        size (str): Size of the generated image. DALL·E 3 supports '1024x1024', '1024x1792', '1792x1024'.
    Returns:
        list: List of URLs of the generated images.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    client = openai.OpenAI(api_key=api_key)
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=input_text,
            n=n,
            size=size,
        )
        return [img.url for img in response.data]
    except Exception as e:
        print(f"Error using DALL·E 3: {e}")
        return []


def download_image_from_url(url: str, use_tempfile: bool = True) -> str:
    """
    Downloads an image from a URL and saves it to a temporary file or to 'debug.png'.
    Returns the local file path to the downloaded image.
    Args:
        url (str): The image URL.
        use_tempfile (bool): If True, saves to a temporary file. If False, saves as 'debug.png'.
    """
    response = requests.get(url)
    response.raise_for_status()
    if use_tempfile:
        suffix = ".png"  # DALL·E images are usually PNG
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name
    else:
        debug_path = "debug.png"
        with open(debug_path, "wb") as f:
            f.write(response.content)
        return debug_path
