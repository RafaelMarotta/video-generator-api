import os
import openai
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def llm(input_data, expected_output=None):
    system_prompt = (
        "You are responsible for splitting a long text into blocks for on-screen display. Follow these rules:\n"
        "- Each block must be a single string in the array.\n"
        "- Each block must not exceed `maxLines * maxCharsLine` total characters.\n"
        "- Never split words inside the block. Always break at spaces between words.\n"
        "- Prefer breaking after punctuation (commas, periods, dashes, etc.) if possible.\n"
        "- Prioritize natural flow and readability.\n"
        "- Output a single array of strings, where each string is a full block of text.\n"
        "- Do not add `\\n` manually. Do not split into arrays of arrays.\n"
        "- If the text is too long, split into as many blocks as needed."
    )

    input_text = (
        f"text: {input_data['text']}\n"
        f"maxLines: {input_data['maxLines']}\n"
        f"maxCharsLine: {input_data['maxCharsLine']}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": input_text},
    ]

    if expected_output:
        messages.append(
            {"role": "user", "content": f"Expected Output: {expected_output}"}
        )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", messages=messages
        )
        return response.model_dump()["choices"][0]["message"]["content"]
    except Exception as e:
        return {"error": str(e)}

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
