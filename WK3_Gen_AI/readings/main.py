import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def generate():
    client = genai.Client(api_key=GEMINI_API_KEY)

    model = "gemini-3-flash-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""hello gemini, can you tell me a joke?"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.HIGH,
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="")


if __name__ == "__main__":
    generate()
