import os
from typing import Optional

from openai import OpenAI
from openai.types.chat.chat_completion import ChatCompletion

# Setup the OpenAI API client.
OPENAI: OpenAI = OpenAI(
    api_key=os.getenv("OPENROUTER_AI_KEY"), base_url="https://openrouter.ai/api/v1"
)

MODEL: str = "openai/gpt-oss-120b:free"
ROLE: str = "user"


def chat(prompt: str) -> Optional[str]:
    """
    Interact with the GPT-3.5 model using the OpenRouter.ai API.

    This function takes a single string argument and returns a string response.
    If the interaction with the model fails, the function returns None instead.
    """
    try:
        response: ChatCompletion = OPENAI.chat.completions.create(
            model="openai/gpt-oss-120b:free",
            messages=[
                {
                    "role": ROLE,
                    "content": prompt,
                }  # type: ignore
            ],
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Exception during LLM call: {e}")
        return None
