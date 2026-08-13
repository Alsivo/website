from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


# =========================================================
# Paths
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

WEBSITE_ROOT = (
    Path(__file__)
    .resolve()
    .parents[2]
)

BLOG_IMAGE_DIR = (
    WEBSITE_ROOT
    / "public"
    / "images"
    / "blog"
)

SOCIAL_OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "social"
    / "images"
)


# =========================================================
# Sizes
# =========================================================

BLOG_WIDTH = 1536
BLOG_HEIGHT = 864

INSTAGRAM_WIDTH = 1080
INSTAGRAM_HEIGHT = 1350


# =========================================================
# Colors
# =========================================================

NAVY = (
    3,
    15,
    35,
)

NAVY_2 = (
    4,
    25,
    58,
)

BLUE = (
    22,
    98,
    220,
)

BLUE_LIGHT = (
    58,
    145,
    255,
)

WHITE = (
    255,
    255,
    255,
)

BLACK = (
    7,
    18,
    36,
)

TEXT_MUTED = (
    82,
    99,
    125,
)

LIGHT_TEXT = (
    220,
    230,
    244,
)

BORDER = (
    224,
    232,
    242,
)

DIVIDER = (
    211,
    220,
    233,
)


# =========================================================
# Fonts
# =========================================================

FONT_CANDIDATES = [
    Path(
        "C:/Windows/Fonts/YuGothB.ttc"
    ),
    Path(
        "C:/Windows/Fonts/YuGothM.ttc"
    ),
    Path(
        "C:/Windows/Fonts/meiryob.ttc"
    ),
    Path(
        "C:/Windows/Fonts/meiryo.ttc"
    ),
]


def find_font() -> Path:
    """利用可能な日本語フォントを探す。"""

    for path in FONT_CANDIDATES:
        if path.exists():
            return path

    raise RuntimeError(
        "使用できる日本語フォントが"
        "見つかりません。"
    )


FONT_PATH = find_font()


def font(
    size: int,
) -> ImageFont.FreeTypeFont:
    """指定サイズのフォントを返す。"""

    return ImageFont.truetype(
        str(FONT_PATH),
        size=size,
    )


# =========================================================
# Text helpers
# =========================================================

PROHIBITED_LINE_START = set(
    "。、！？!?)]）】』」〉》〕"
    "ぁぃぅぇぉゃゅょっ"
    "ァィゥェォャュョッ"
    "ー〜"
)

PROHIBITED_LINE_END = set(
    "([（【『「〈《〔"
)


def clean_text(
    value: Any,
) -> str:
    """表示用文字列を整える。"""

    if value is None:
        return ""

    text = str(
        value
    )

    text = text.replace(
        "\r",
        " ",
    ).replace(
        "\n",
        " ",
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
) -> int:
    """文字列の描画幅を取得する。"""

    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=text_font,
    )

    return (
        bbox[2]
        - bbox[0]
    )


def text_height(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
) -> int:
    """文字列の描画高さを取得する。"""

    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=text_font,
    )

    return (
        bbox[3]
        - bbox[1]
    )


# =========================================================
# Normal text wrapping
# =========================================================

def find_break_index(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> int:
    """
    descriptionなどの通常文章用。
    幅を超えない範囲で改行位置を探す。
    """

    if not text:
        return 0

    best = 0

    for index in range(
        1,
        len(text) + 1,
    ):
        candidate = text[
            :index
        ]

        if (
            text_width(
                draw,
                candidate,
                text_font,
            )
            <= max_width
        ):
            best = index
        else:
            break

    if best >= len(text):
        return len(text)

    if best <= 0:
        return 1

    while (
        best < len(text)
        and text[best]
        in PROHIBITED_LINE_START
        and best > 1
    ):
        best -= 1

    while (
        best > 1
        and text[
            best - 1
        ]
        in PROHIBITED_LINE_END
    ):
        best -= 1

    preferred_breaks = (
        "？",
        "?",
        "！",
        "!",
        "。",
        "、",
        "・",
        "｜",
        "|",
        "：",
        ":",
        "／",
        "/",
        " ",
    )

    search_start = max(
        1,
        int(
            best * 0.62
        ),
    )

    for index in range(
        best - 1,
        search_start - 1,
        -1,
    ):
        if (
            text[index]
            in preferred_breaks
        ):
            return (
                index + 1
            )

    return max(
        1,
        best,
    )


def rebalance_lines(
    lines: list[str],
) -> list[str]:
    """descriptionの最終行が極端に短くなる状態を軽減する。"""

    if len(lines) < 2:
        return lines

    updated = lines[:]

    if len(
        updated[-1]
    ) <= 3:

        previous = updated[-2]

        if len(previous) >= 6:

            move_count = min(
                4,
                max(
                    2,
                    len(previous) // 4,
                ),
            )

            moved = previous[
                -move_count:
            ]

            updated[-2] = previous[
                :-move_count
            ].rstrip()

            updated[-1] = (
                moved
                + updated[-1]
            ).lstrip()

    return updated


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
    ellipsis: bool = False,
) -> list[str]:
    """通常文章用の日本語自動改行。"""

    text = clean_text(
        text
    )

    if not text:
        return []

    lines = []

    rest = text

    while (
        rest
        and len(lines)
        < max_lines
    ):

        if (
            text_width(
                draw,
                rest,
                text_font,
            )
            <= max_width
        ):
            lines.append(
                rest
            )
            rest = ""
            break

        break_index = (
            find_break_index(
                draw,
                rest,
                text_font,
                max_width,
            )
        )

        line = rest[
            :break_index
        ].strip()

        rest = rest[
            break_index:
        ].strip()

        if not line:
            line = rest[:1]
            rest = rest[1:]

        lines.append(
            line
        )

    lines = rebalance_lines(
        lines
    )

    if (
        rest
        and lines
        and ellipsis
    ):

        last = lines[-1]

        while (
            last
            and text_width(
                draw,
                last + "…",
                text_font,
            )
            > max_width
        ):
            last = last[:-1]

        lines[-1] = (
            last.rstrip()
            + "…"
        )

    return lines


# =========================================================
# AI title layout helpers
# =========================================================

def get_ai_title_lines(
    article: dict[str, Any],
    key: str,
) -> list[str]:
    """
    generate_images.pyでAIが生成した
    改行済みタイトルを取得する。
    """

    raw_lines = article.get(
        key,
        [],
    )

    if not isinstance(
        raw_lines,
        list,
    ):
        return []

    lines = []

    for raw_line in raw_lines:

        line = clean_text(
            raw_line
        )

        if line:
            lines.append(
                line
            )

    return lines


def validate_ai_title_lines(
    title: str,
    lines: list[str],
) -> bool:
    """
    AIがタイトルを書き換えていないか確認する。
    改行だけならTrue。
    """

    if not lines:
        return False

    original = re.sub(
        r"\s+",
        "",
        clean_text(
            title
        ),
    )

    reconstructed = re.sub(
        r"\s+",
        "",
        "".join(
            lines
        ),
    )

    return (
        original
        == reconstructed
    )


def split_long_title_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    max_width: int,
    max_lines: int,
    check_font_size: int,
) -> list[str]:
    """
    AIが決めた意味的な改行をできるだけ維持しつつ、
    画像上で長すぎる行だけ追加分割する。

    ・AI改行は原則維持
    ・長すぎる行だけ分割
    ・記号など自然な位置を優先
    ・最大行数を超えない
    """

    if not lines:
        return []

    check_font = font(
        check_font_size
    )

    result: list[str] = []

    for line_index, line in enumerate(
        lines
    ):

        remaining_original_lines = (
            len(lines)
            - line_index
            - 1
        )

        available_slots = (
            max_lines
            - len(result)
            - remaining_original_lines
        )

        # これ以上分割すると最大行数を超える場合は
        # AIの行をそのまま使用する。
        if available_slots <= 1:

            result.append(
                line
            )

            continue

        # 十分収まっている行はAI改行をそのまま維持。
        if (
            text_width(
                draw,
                line,
                check_font,
            )
            <= max_width
        ):

            result.append(
                line
            )

            continue

        rest = line

        while rest:

            # 残りがそのまま収まるなら終了。
            if (
                text_width(
                    draw,
                    rest,
                    check_font,
                )
                <= max_width
            ):

                result.append(
                    rest
                )

                break

            remaining_original_lines = (
                len(lines)
                - line_index
                - 1
            )

            slots_left = (
                max_lines
                - len(result)
                - remaining_original_lines
            )

            # これ以上安全に分割できない。
            if slots_left <= 1:

                result.append(
                    rest
                )

                break

            break_index = find_break_index(
                draw=draw,
                text=rest,
                text_font=check_font,
                max_width=max_width,
            )

            if (
                break_index <= 0
                or break_index >= len(rest)
            ):

                result.append(
                    rest
                )

                break

            first = rest[
                :break_index
            ].strip()

            second = rest[
                break_index:
            ].strip()

            if (
                not first
                or not second
            ):

                result.append(
                    rest
                )

                break

            result.append(
                first
            )

            rest = second

    return result


def fixed_prebroken_title(
    lines: list[str],
    font_size: int,
) -> tuple[
    ImageFont.FreeTypeFont,
    list[str],
]:
    """
    AIが決めた改行をそのまま使用し、
    指定した固定フォントサイズを返す。
    """

    return (
        font(font_size),
        lines,
    )


def fit_prebroken_title(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    max_width: int,
    max_font_size: int,
    min_font_size: int,
) -> ImageFont.FreeTypeFont:
    """
    AIが決めた改行位置を変更せず、
    全行が収まる最大フォントサイズを探す。
    """

    for size in range(
        max_font_size,
        min_font_size - 1,
        -2,
    ):

        title_font = font(
            size
        )

        fits = all(
            text_width(
                draw,
                line,
                title_font,
            )
            <= max_width
            for line in lines
        )

        if fits:
            return title_font

    return font(
        min_font_size
    )


def fallback_title_lines(
    draw: ImageDraw.ImageDraw,
    title: str,
    max_width: int,
    max_lines: int,
    max_font_size: int,
    min_font_size: int,
) -> tuple[
    ImageFont.FreeTypeFont,
    list[str],
]:
    """
    AI改行が取得できなかった場合だけ使用する
    シンプルなフォールバック。
    """

    cleaned_title = clean_text(
        title
    )

    for size in range(
        max_font_size,
        min_font_size - 1,
        -2,
    ):

        title_font = font(
            size
        )

        lines = wrap_text(
            draw=draw,
            text=cleaned_title,
            text_font=title_font,
            max_width=max_width,
            max_lines=max_lines,
            ellipsis=False,
        )

        reconstructed = re.sub(
            r"\s+",
            "",
            "".join(
                lines
            ),
        )

        original = re.sub(
            r"\s+",
            "",
            cleaned_title,
        )

        if (
            reconstructed
            == original
            and len(lines)
            <= max_lines
        ):
            return (
                title_font,
                lines,
            )

    fallback_font = font(
        min_font_size
    )

    fallback_lines = wrap_text(
        draw=draw,
        text=cleaned_title,
        text_font=fallback_font,
        max_width=max_width,
        max_lines=max_lines,
        ellipsis=True,
    )

    return (
        fallback_font,
        fallback_lines,
    )

# =========================================================
# Image title settings
# =========================================================

BLOG_TITLE_FONT_SIZE = 64
INSTAGRAM_TITLE_FONT_SIZE = 44

BLOG_TITLE_LINE_GAP = 6
INSTAGRAM_TITLE_LINE_GAP = 8

def prepare_title(
    draw: ImageDraw.ImageDraw,
    article: dict[str, Any],
    title: str,
    ai_key: str,
    max_width: int,
    max_lines: int,
    max_font_size: int,
    min_font_size: int,
) -> tuple[
    ImageFont.FreeTypeFont,
    list[str],
]:
    """
    AI改行を最優先する。

    ただしAIが作った1行が画像上で長すぎる場合は、
    意味的な改行をできるだけ維持しながら
    長い行だけ追加分割する。

    最後にフォントサイズを調整して
    全行を確実に画像内へ収める。
    """

    ai_lines = get_ai_title_lines(
        article,
        ai_key,
    )

    if (
        ai_lines
        and len(ai_lines)
        <= max_lines
        and validate_ai_title_lines(
            title,
            ai_lines,
        )
    ):

        # -------------------------------------------------
        # AI改行をベースに、
        # 長すぎる行だけ追加分割
        #
        # 最大フォントサイズより少し小さいサイズを
        # 判定基準にすることで、
        # 不必要な分割を避ける。
        # -------------------------------------------------

        check_font_size = max(
            min_font_size,
            max_font_size - 8,
        )

        adjusted_lines = (
            split_long_title_lines(
                draw=draw,
                lines=ai_lines,
                max_width=max_width,
                max_lines=max_lines,
                check_font_size=check_font_size,
            )
        )

        # タイトル文字列が壊れていないことを再確認。
        if (
            adjusted_lines
            and len(adjusted_lines)
            <= max_lines
            and validate_ai_title_lines(
                title,
                adjusted_lines,
            )
        ):

            title_font = (
                fit_prebroken_title(
                    draw=draw,
                    lines=adjusted_lines,
                    max_width=max_width,
                    max_font_size=max_font_size,
                    min_font_size=min_font_size,
                )
            )

            # min_font_sizeでも幅を超えるような
            # 異常ケースはfallbackへ回す。
            if all(
                text_width(
                    draw,
                    line,
                    title_font,
                )
                <= max_width
                for line in adjusted_lines
            ):

                return (
                    title_font,
                    adjusted_lines,
                )

    return fallback_title_lines(
        draw=draw,
        title=title,
        max_width=max_width,
        max_lines=max_lines,
        max_font_size=max_font_size,
        min_font_size=min_font_size,
    )

def interpolate_color(
    color_1: tuple[
        int,
        int,
        int,
    ],
    color_2: tuple[
        int,
        int,
        int,
    ],
    ratio: float,
) -> tuple[
    int,
    int,
    int,
]:

    return tuple(
        int(
            color_1[index]
            + (
                color_2[index]
                - color_1[index]
            )
            * ratio
        )
        for index in range(3)
    )


def draw_gradient(
    image: Image.Image,
) -> None:
    """ALSIVO共通背景。"""

    width, height = image.size

    draw = ImageDraw.Draw(
        image
    )

    for y in range(
        height
    ):

        ratio = (
            y
            / max(
                1,
                height - 1,
            )
        )

        color = interpolate_color(
            NAVY,
            NAVY_2,
            ratio,
        )

        draw.line(
            (
                0,
                y,
                width,
                y,
            ),
            fill=color,
        )


def draw_wave(
    draw: ImageDraw.ImageDraw,
    width: int,
    base_y: int,
    amplitude: int,
    height: int,
    alpha_factor: float = 1.0,
) -> None:
    """ALSIVO共通の波線装飾。"""

    del alpha_factor

    for offset in range(
        0,
        height,
        12,
    ):

        points = []

        for x in range(
            -100,
            width + 100,
            20,
        ):

            y = (
                base_y
                + offset
                + int(
                    amplitude
                    * math.sin(
                        x / 120
                    )
                )
            )

            points.append(
                (
                    x,
                    y,
                )
            )

        draw.line(
            points,
            fill=(
                34,
                105,
                238,
            ),
            width=1,
        )


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    box: tuple[
        int,
        int,
        int,
        int,
    ],
    text: str,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[
        int,
        int,
        int,
    ],
) -> None:
    """ボックス中央に文字を描画する。"""

    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        text,
        font=text_font,
    )

    text_w = (
        bbox[2]
        - bbox[0]
    )

    text_h = (
        bbox[3]
        - bbox[1]
    )

    x1, y1, x2, y2 = box

    x = (
        x1
        + (
            x2
            - x1
            - text_w
        )
        / 2
    )

    y = (
        y1
        + (
            y2
            - y1
            - text_h
        )
        / 2
        - bbox[1]
    )

    draw.text(
        (
            x,
            y,
        ),
        text,
        font=text_font,
        fill=fill,
    )


def draw_brand(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    large: bool = True,
) -> None:
    """ALSIVOロゴ領域。"""

    logo_size = (
        56
        if large
        else 48
    )

    tagline_size = (
        21
        if large
        else 19
    )

    draw.text(
        (
            x,
            y,
        ),
        "ALSIVO",
        font=font(
            logo_size
        ),
        fill=WHITE,
    )

    draw.text(
        (
            x,
            y + 62,
        ),
        "AIを、もっとわかりやすく。",
        font=font(
            tagline_size
        ),
        fill=LIGHT_TEXT,
    )


def draw_badge(
    draw: ImageDraw.ImageDraw,
    box: tuple[
        int,
        int,
        int,
        int,
    ],
    label: str,
) -> None:
    """カテゴリバッジ。"""

    draw.rounded_rectangle(
        box,
        radius=40,
        fill=BLUE,
    )

    draw_centered_text(
        draw,
        box,
        label,
        font(
            28
        ),
        WHITE,
    )


# =========================================================
# Article helpers
# =========================================================

def get_category(
    article: dict[str, Any],
) -> str:

    category = clean_text(
        article.get(
            "category"
        )
    )

    return (
        category
        if category
        else "AIツール"
    )


def get_tags(
    article: dict[str, Any],
) -> list[str]:
    """Instagram下部に表示するタグを取得する。"""

    raw_tags = article.get(
        "tags",
        [],
    )

    if not isinstance(
        raw_tags,
        list,
    ):
        return []

    tags = []

    for raw_tag in raw_tags:

        tag = clean_text(
            raw_tag
        )

        if (
            tag
            and tag not in tags
        ):
            tags.append(
                tag
            )

    return tags[:3]


def get_description(
    article: dict[str, Any],
) -> str:

    return clean_text(
        article.get(
            "description",
            "",
        )
    )


def validate_article(
    article: dict[str, Any],
) -> None:
    """画像生成に最低限必要な情報を確認する。"""

    for key in (
        "slug",
        "title",
    ):

        if not clean_text(
            article.get(
                key
            )
        ):
            raise ValueError(
                f"{key}がありません。"
            )


# =========================================================
# Blog 16:9
# =========================================================

def create_blog_image(
    article: dict[str, Any],
    output_path: Path | None = None,
) -> Path:
    """
    ブログ用16:9画像を生成する。

    Blog版はSNS用と役割を分け、
    ブランドロゴやURLは表示せず、
    記事内容そのものを主役にする。
    """

    validate_article(
        article
    )

    slug = clean_text(
        article["slug"]
    )

    title = clean_text(
        article["title"]
    )

    category = get_category(
        article
    )

    description = get_description(
        article
    )

    if output_path is None:

        BLOG_IMAGE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            BLOG_IMAGE_DIR
            / f"{slug}.png"
        )

    else:

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    # =====================================================
    # Canvas
    # =====================================================

    image = Image.new(
        "RGB",
        (
            BLOG_WIDTH,
            BLOG_HEIGHT,
        ),
        NAVY,
    )

    draw_gradient(
        image
    )

    draw = ImageDraw.Draw(
        image
    )

    # =====================================================
    # Main white card
    #
    # ALSIVOロゴ領域をなくした分、
    # カードを画面中央へ大きく配置する。
    # =====================================================

    card = (
        64,
        72,
        BLOG_WIDTH - 64,
        BLOG_HEIGHT - 72,
    )

    draw.rounded_rectangle(
        card,
        radius=40,
        fill=WHITE,
        outline=BORDER,
        width=2,
    )

    # =====================================================
    # Category
    # =====================================================

    badge = (
        110,
        120,
        410,
        184,
    )

    draw_badge(
        draw,
        badge,
        category,
    )

    # =====================================================
    # Title
    #
    # generate_images.pyでAIが決めた
    # blog_title_linesを最優先する。
    # =====================================================

    title_x = 110
    title_y = 245

    title_max_width = (
        BLOG_WIDTH
        - title_x
        - 120
    )

    title_font, title_lines = prepare_title(
        draw=draw,
        article=article,
        title=title,
        ai_key="blog_title_lines",
        max_width=title_max_width,
        max_lines=3,
        max_font_size=BLOG_TITLE_FONT_SIZE,
        min_font_size=54,
    )

    current_y = title_y

    line_gap = BLOG_TITLE_LINE_GAP

    for line in title_lines:

        draw.text(
            (
                title_x,
                current_y,
            ),
            line,
            font=title_font,
            fill=BLUE,
        )

        current_y += (
            text_height(
                draw,
                line,
                title_font,
            )
            + line_gap
        )

    # =====================================================
    # Divider
    # =====================================================

    divider_y = max(
        current_y + 18,
        520,
    )

    divider_y = min(
        divider_y,
        585,
    )

    draw.line(
        (
            title_x,
            divider_y,
            BLOG_WIDTH - 300,
            divider_y,
        ),
        fill=DIVIDER,
        width=2,
    )

    # =====================================================
    # Description
    # =====================================================

    description_font = font(
        27
    )

    description_lines = wrap_text(
        draw=draw,
        text=description,
        text_font=description_font,
        max_width=1180,
        max_lines=3,
        ellipsis=True,
    )

    description_y = (
        divider_y + 34
    )

    for line in description_lines:

        draw.text(
            (
                title_x,
                description_y,
            ),
            line,
            font=description_font,
            fill=TEXT_MUTED,
        )

        description_y += 43

    # =====================================================
    # Very subtle decoration
    #
    # 意味のないAIイラストは使わず、
    # ALSIVOの背景デザインだけ薄く残す。
    # =====================================================

    draw_wave(
        draw=draw,
        width=BLOG_WIDTH,
        base_y=755,
        amplitude=24,
        height=100,
    )

    # =====================================================
    # Save
    # =====================================================

    image.save(
        output_path,
        format="PNG",
        optimize=True,
    )

    return output_path

def create_instagram_image(
    article: dict[str, Any],
    output_path: Path | None = None,
) -> Path:
    """Instagram用4:5画像を生成する。"""

    validate_article(
        article
    )

    slug = clean_text(
        article["slug"]
    )

    title = clean_text(
        article["title"]
    )

    category = get_category(
        article
    )

    description = get_description(
        article
    )

    tags = get_tags(
        article
    )

    if output_path is None:

        SOCIAL_OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = (
            SOCIAL_OUTPUT_DIR
            / f"{slug}-instagram.png"
        )

    else:

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    image = Image.new(
        "RGB",
        (
            INSTAGRAM_WIDTH,
            INSTAGRAM_HEIGHT,
        ),
        NAVY,
    )

    draw_gradient(
        image
    )

    draw = ImageDraw.Draw(
        image
    )

    draw_brand(
        draw,
        56,
        40,
        large=False,
    )

    card = (
        45,
        185,
        1035,
        1010,
    )

    draw.rounded_rectangle(
        card,
        radius=34,
        fill=WHITE,
        outline=BORDER,
        width=2,
    )

    badge = (
        85,
        225,
        390,
        296,
    )

    draw_badge(
        draw,
        badge,
        category,
    )

    title_x = 85
    title_y = 350

    title_max_width = (
        1035
        - title_x
        - 65
    )

    # -----------------------------------------------------
    # AIが意味を理解して決めた改行を最優先
    # -----------------------------------------------------

    title_font, title_lines = prepare_title(
        draw=draw,
        article=article,
        title=title,
        ai_key="instagram_title_lines",
        max_width=title_max_width,
        max_lines=5,
        max_font_size=INSTAGRAM_TITLE_FONT_SIZE,
        min_font_size=38,
    )

    current_y = title_y

    line_gap = INSTAGRAM_TITLE_LINE_GAP

    for line in title_lines:

        draw.text(
            (
                title_x,
                current_y,
            ),
            line,
            font=title_font,
            fill=BLUE,
        )

        current_y += (
            text_height(
                draw,
                line,
                title_font,
            )
            + line_gap
        )

    divider_y = max(
        current_y + 22,
        620,
    )

    divider_y = min(
        divider_y,
        735,
    )

    draw.line(
        (
            85,
            divider_y,
            760,
            divider_y,
        ),
        fill=DIVIDER,
        width=2,
    )

    description_font = font(
        27
    )

    description_lines = wrap_text(
        draw=draw,
        text=description,
        text_font=description_font,
        max_width=820,
        max_lines=3,
        ellipsis=True,
    )

    description_y = (
        divider_y + 30
    )

    for line in description_lines:

        draw.text(
            (
                85,
                description_y,
            ),
            line,
            font=description_font,
            fill=BLACK,
        )

        description_y += 42

    draw_wave(
        draw=draw,
        width=INSTAGRAM_WIDTH,
        base_y=1030,
        amplitude=28,
        height=250,
    )

    if not tags:
        tags = [
            category,
        ]

    chip_count = min(
        len(tags),
        3,
    )

    chip_gap = 30
    total_margin = 80

    available_width = (
        INSTAGRAM_WIDTH
        - total_margin * 2
        - chip_gap
        * (
            chip_count - 1
        )
    )

    chip_width = int(
        available_width
        / chip_count
    )

    chip_y1 = 1065
    chip_y2 = 1138

    for index, tag in enumerate(
        tags[:3]
    ):

        x1 = (
            total_margin
            + index
            * (
                chip_width
                + chip_gap
            )
        )

        x2 = (
            x1
            + chip_width
        )

        chip_box = (
            x1,
            chip_y1,
            x2,
            chip_y2,
        )

        draw.rounded_rectangle(
            chip_box,
            radius=36,
            fill=NAVY,
            outline=BLUE_LIGHT,
            width=3,
        )

        chip_font = font(
            24
        )

        chip_label = tag

        while (
            len(chip_label) > 1
            and text_width(
                draw,
                chip_label,
                chip_font,
            )
            > chip_width - 40
        ):

            chip_label = (
                chip_label[:-1]
            )

        if chip_label != tag:

            chip_label = (
                chip_label.rstrip()
                + "…"
            )

        draw_centered_text(
            draw,
            chip_box,
            chip_label,
            chip_font,
            WHITE,
        )

    cta_box = (
        45,
        1220,
        1035,
        1315,
    )

    draw.rounded_rectangle(
        cta_box,
        radius=48,
        fill=BLUE,
    )

    draw.text(
        (
            80,
            1248,
        ),
        "詳しくはプロフィールのリンクからチェック！",
        font=font(
            24
        ),
        fill=WHITE,
    )

    website_text = (
        "alsivo.com"
    )

    website_font = font(
        23
    )

    website_width = text_width(
        draw,
        website_text,
        website_font,
    )

    draw.text(
        (
            990
            - website_width,
            1249,
        ),
        website_text,
        font=website_font,
        fill=WHITE,
    )

    image.save(
        output_path,
        format="PNG",
        optimize=True,
    )

    return output_path


# =========================================================
# Combined generator
# =========================================================

def generate_article_images(
    article: dict[str, Any],
) -> tuple[
    Path,
    Path,
]:
    """
    1記事から
    Blog 16:9 + Instagram 4:5
    を生成する。
    """

    print(
        "[Image Generator] "
        "ブログ画像を生成中..."
    )

    blog_path = (
        create_blog_image(
            article
        )
    )

    print(
        "[Image Generator] "
        "Instagram画像を生成中..."
    )

    instagram_path = (
        create_instagram_image(
            article
        )
    )

    print(
        "\n===== ALSIVO Image Generator ====="
    )

    print(
        f"Blog：{blog_path}"
    )

    print(
        f"Instagram：{instagram_path}"
    )

    return (
        blog_path,
        instagram_path,
    )