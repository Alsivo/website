import base64
import re
from pathlib import Path
from typing import Any

from openai import OpenAI

from config import (
    IMAGE_MODEL,
    IMAGE_OUTPUT_FORMAT,
    IMAGE_QUALITY,
    IMAGE_SIZE,
    MODEL,
    OPENAI_API_KEY,
)


client = OpenAI(
    api_key=OPENAI_API_KEY,
    timeout=300.0,
    max_retries=2,
)


WEBSITE_ROOT = Path(__file__).resolve().parents[2]
IMAGE_DIRECTORY = (
    WEBSITE_ROOT
    / "public"
    / "images"
    / "blog"
)
BACKGROUND_DIRECTORY = WEBSITE_ROOT / "public" / "images" / "article-backgrounds"


def validate_slug(slug: str) -> str:
    """画像ファイル名に利用できるslugか確認する。"""

    cleaned_slug = slug.strip().lower()

    if not cleaned_slug:
        raise ValueError(
            "画像生成に必要なslugが未入力です。"
        )

    if not re.fullmatch(
        r"[a-z0-9]+(?:-[a-z0-9]+)*",
        cleaned_slug,
    ):
        raise ValueError(
            "slugには半角英小文字、数字、"
            "ハイフンだけを使用してください。"
            f" 現在のslug：{cleaned_slug}"
        )

    return cleaned_slug


def create_image_prompt(
    article: dict[str, Any],
) -> str:
    """記事情報からアイキャッチ画像の指示文を作る。"""

    return (
        "Create a photorealistic background photograph for a Japanese "
        "technology media website article. Anime characters and speech bubbles "
        "will be overlaid later.\n\n"
        f"Article title: {article['title']}\n"
        f"Article description: {article['description']}\n"
        f"Category: {article['category']}\n"
        f"Tags: {', '.join(article['tags'])}\n\n"
        "Visual direction:\n"
        "- genuinely photorealistic editorial photography, not an illustration\n"
        "- clean composition with one clear focal point\n"
        "- a realistic everyday scene and objects directly related to the article topic\n"
        "- subtle depth and soft natural lighting\n"
        "- suitable for a professional AI and productivity website\n"
        "- landscape composition with safe space around the edges\n"
        "- do not use recognizable company logos\n"
        "- do not show copyrighted product interfaces\n"
        "- no people or characters\n"
        "- keep the upper-left and lower-right areas calm for character overlays\n"
        "- no words, letters, numbers, captions, UI text, or logos\n"
        "- avoid generic robot heads and glowing human brains\n"
    )


def generate_article_image(
    article: dict[str, Any],
) -> tuple[str, Path]:
    """
    記事のアイキャッチ画像を生成してpublicへ保存する。

    戻り値はWebsiteから使用するURL。
    """

    slug = validate_slug(article["slug"])
    prompt = create_image_prompt(article)

    print("[Image Agent] 画像生成を開始...")

    response = client.responses.create(
        model=MODEL,
        store=False,
        input=prompt,
        tools=[
            {
                "type": "image_generation",
                "model": IMAGE_MODEL,
                "size": IMAGE_SIZE,
                "quality": IMAGE_QUALITY,
                "output_format": IMAGE_OUTPUT_FORMAT,
                "background": "opaque",
            }
        ],
        tool_choice={
            "type": "image_generation",
        },
    )

    image_base64: str | None = None

    for output_item in response.output:
        if (
            getattr(
                output_item,
                "type",
                None,
            )
            == "image_generation_call"
        ):
            image_base64 = getattr(
                output_item,
                "result",
                None,
            )

            if image_base64:
                break

    if not image_base64:
        raise RuntimeError(
            "生成画像のデータを取得できませんでした。"
        )

    try:
        image_bytes = base64.b64decode(
            image_base64,
            validate=True,
        )
    except ValueError as error:
        raise RuntimeError(
            "生成画像のデコードに失敗しました。"
        ) from error

    IMAGE_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_name = (
        f"{slug}.{IMAGE_OUTPUT_FORMAT}"
    )
    output_path = IMAGE_DIRECTORY / file_name

    output_path.write_bytes(image_bytes)

    BACKGROUND_DIRECTORY.mkdir(parents=True, exist_ok=True)
    background_path = BACKGROUND_DIRECTORY / file_name
    background_path.write_bytes(image_bytes)

    print(
        "[Image Agent] 画像を保存しました："
        f"{output_path}"
    )

    return (
        f"/images/blog/{file_name}",
        output_path,
    )
