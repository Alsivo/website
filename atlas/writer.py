from openai import OpenAI
from config import OPENAI_API_KEY, MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_article(topic: str):

    response = client.responses.create(
        model=MODEL,
        input=f"{topic}について記事を書いて"
    )

    return response.output_text