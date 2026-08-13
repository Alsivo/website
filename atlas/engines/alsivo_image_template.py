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

WEBSITE_ROOT = Path(__file__).resolve().parents[2]

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
# Canvas
# =========================================================

BLOG_WIDTH = 1536
BLOG_HEIGHT = 864

INSTAGRAM_WIDTH = 1080
INSTAGRAM_HEIGHT = 1350


# =========================================================
# ALSIVO colors
# =========================================================

NAVY = (3, 15, 35)
NAVY_2 = (4, 25, 58)

BLUE = (22, 98, 220)
BLUE_DARK = (8, 73, 188)
LIGHT_BLUE = (72, 157, 255)

WHITE = (255, 255, 255)
BLACK = (7, 18, 36)

MUTED = (215, 226, 242)
TEXT_MUTED = (82, 99, 125)

CARD_BORDER = (224, 232, 242)
DIVIDER = (211, 220, 233)


# =========================================================
# Fonts
# =========================================================

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/YuGothB.ttc"),
    Path("C:/Windows/Fonts/YuGothM.ttc"),
    Path("C:/Windows/Fonts/meiryob.ttc"),
    Path("C:/Windows/Fonts/meiryo.ttc"),
]


def find_font() -> Path:
    for path in FONT_CANDIDATES:
        if path.exists():
            return path

    raise RuntimeError(
        "使用できる日本語フォントが見つかりません。"
    )


FONT_PATH = find_font()


def font(
    size: int,
) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(
        str(FONT_PATH),
        size=size,
    )


# =========================================================
# Text rules
# =========================================================

# 行頭に来てほしくない文字
PROHIBITED_LINE_START = set(
    "、。，．・：；？！"
    ")]}）〕］｝〉》」』】"
    "ぁぃぅぇぉっゃゅょ"
    "ァィゥェォッャュョ"
    "ー〜～"
)

# 行末に残してほしくない文字
PROHIBITED_LINE_END = set(
    "([{（〔［｛〈《「『【"
)


# =========================================================
# Utility
# =========================================================

def clean_text(
    value: Any,
) -> str:
    if value is None:
        return ""

    text = str(value)

    text = (
        text
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text


def text_width(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
) -> int:
    bbox = draw.textbbox(
        (0, 0),
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
    bbox = draw.textbbox(
        (0, 0),
        text,
        font=text_font,
    )

    return (
        bbox[3]
        - bbox[1]
    )


def interpolate_color(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    ratio: float,
) -> tuple[int, int, int]:

    return tuple(
        int(
            start[index]
            + (
                end[index]
                - start[index]
            )
            * ratio
        )
        for index in range(3)
    )


# =========================================================
# Background
# =========================================================

def draw_gradient(
    image: Image.Image,
) -> None:

    width, height = image.size

    draw = ImageDraw.Draw(
        image
    )

    for y in range(height):

        ratio = (
            y
            / max(
                height - 1,
                1,
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
    wave_height: int,
) -> None:

    for offset in range(
        0,
        wave_height,
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
                        x / 130
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
                23,
                94,
                208,
            ),
            width=1,
        )


def draw_soft_decorations(
    draw: ImageDraw.ImageDraw,
    width: int,
    height: int,
) -> None:
    """
    ブログ背景右側の薄い抽象装飾。
    記事固有Visualではなく、
    ALSIVO共通の軽い装飾として使う。
    """

    center_x = int(
        width * 0.79
    )

    center_y = int(
        height * 0.47
    )

    for radius, alpha_color in [
        (
            230,
            (226, 239, 255),
        ),
        (
            170,
            (235, 245, 255),
        ),
        (
            110,
            (243, 249, 255),
        ),
    ]:

        draw.ellipse(
            (
                center_x - radius,
                center_y - radius,
                center_x + radius,
                center_y + radius,
            ),
            fill=alpha_color,
        )

    # ドット
    for row in range(8):
        for column in range(8):

            x = (
                width
                - 290
                + column
                * 24
            )

            y = (
                215
                + row
                * 24
            )

            radius = max(
                2,
                7 - row // 2,
            )

            draw.ellipse(
                (
                    x - radius,
                    y - radius,
                    x + radius,
                    y + radius,
                ),
                fill=(
                    215,
                    232,
                    255,
                ),
            )


# =========================================================
# Brand
# =========================================================

def draw_brand(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    logo_size: int,
    tagline_size: int,
) -> None:

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
            x + 2,
            y + logo_size + 8,
        ),
        "AIを、もっとわかりやすく。",
        font=font(
            tagline_size
        ),
        fill=MUTED,
    )


# =========================================================
# Japanese line wrapping
# =========================================================

def find_best_break_point(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> int:
    """
    max_width内で最も自然な改行位置を探す。
    """

    if not text:
        return 0

    best = 0

    for index in range(
        1,
        len(text) + 1,
    ):

        candidate = (
            text[:index]
        )

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

    # -----------------------------------------------------
    # 行頭禁則
    # -----------------------------------------------------

    while (
        best < len(text)
        and text[best]
        in PROHIBITED_LINE_START
        and best > 1
    ):
        best -= 1

    # -----------------------------------------------------
    # 行末禁則
    # -----------------------------------------------------

    while (
        best > 1
        and text[
            best - 1
        ]
        in PROHIBITED_LINE_END
    ):
        best -= 1

    # -----------------------------------------------------
    # 記号・区切りを優先
    # -----------------------------------------------------

    search_start = max(
        1,
        int(
            best * 0.58
        ),
    )

    preferred_chars = (
        "｜|／/・、，：:"
        "！？?!"
    )

    preferred_break = None

    for index in range(
        best - 1,
        search_start - 1,
        -1,
    ):

        if (
            text[index]
            in preferred_chars
        ):
            preferred_break = (
                index + 1
            )

            break

    if preferred_break:
        best = preferred_break

    return max(
        1,
        best,
    )


def wrap_japanese_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
    max_lines: int,
    add_ellipsis: bool = True,
) -> list[str]:

    text = clean_text(
        text
    )

    if not text:
        return []

    lines: list[str] = []

    remaining = text

    while (
        remaining
        and len(lines)
        < max_lines
    ):

        if (
            text_width(
                draw,
                remaining,
                text_font,
            )
            <= max_width
        ):
            lines.append(
                remaining
            )

            remaining = ""

            break

        break_point = (
            find_best_break_point(
                draw=draw,
                text=remaining,
                text_font=text_font,
                max_width=max_width,
            )
        )

        line = (
            remaining[
                :break_point
            ]
            .strip()
        )

        remaining = (
            remaining[
                break_point:
            ]
            .strip()
        )

        if not line:
            line = remaining[0]

            remaining = (
                remaining[1:]
            )

        lines.append(
            line
        )

    if (
        remaining
        and lines
        and add_ellipsis
    ):

        last_line = lines[-1]

        while (
            last_line
            and text_width(
                draw,
                last_line + "…",
                text_font,
            )
            > max_width
        ):
            last_line = (
                last_line[:-1]
            )

        lines[-1] = (
            last_line.rstrip()
            + "…"
        )

    return lines


def fit_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_lines: int,
    start_size: int,
    min_size: int,
) -> tuple[
    ImageFont.FreeTypeFont,
    list[str],
]:

    cleaned = clean_text(
        text
    )

    for size in range(
        start_size,
        min_size - 1,
        -2,
    ):

        current_font = font(
            size
        )

        lines = (
            wrap_japanese_text(
                draw=draw,
                text=cleaned,
                text_font=current_font,
                max_width=max_width,
                max_lines=max_lines,
                add_ellipsis=False,
            )
        )

        reconstructed = "".join(
            line.replace(
                " ",
                "",
            )
            for line in lines
        )

        source_compact = (
            cleaned.replace(
                " ",
                "",
            )
        )

        if (
            reconstructed
            == source_compact
        ):
            return (
                current_font,
                lines,
            )

    final_font = font(
        min_size
    )

    final_lines = (
        wrap_japanese_text(
            draw=draw,
            text=cleaned,
            text_font=final_font,
            max_width=max_width,
            max_lines=max_lines,
            add_ellipsis=True,
        )
    )

    return (
        final_font,
        final_lines,
    )


def draw_text_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    x: int,
    y: int,
    text_font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
    line_spacing: float = 1.23,
    final_line_blue: bool = False,
) -> int:

    current_y = y

    line_height = int(
        text_font.size
        * line_spacing
    )

    for index, line in enumerate(
        lines
    ):

        line_fill = fill

        if (
            final_line_blue
            and index
            == len(lines) - 1
        ):
            line_fill = BLUE

        draw.text(
            (
                x,
                current_y,
            ),
            line,
            font=text_font,
            fill=line_fill,
        )

        current_y += (
            line_height
        )

    return current_y


# =========================================================
# Article helpers
# =========================================================

def get_title(
    article: dict[str, Any],
) -> str:

    title = clean_text(
        article.get(
            "title",
            "",
        )
    )

    if not title:
        raise ValueError(
            "titleがありません。"
        )

    return title


def get_description(
    article: dict[str, Any],
) -> str:

    return clean_text(
        article.get(
            "description",
            "",
        )
    )


def get_category(
    article: dict[str, Any],
) -> str:

    category = clean_text(
        article.get(
            "category",
            "",
        )
    )

    return (
        category
        if category
        else "AIガイド"
    )


def get_slug(
    article: dict[str, Any],
) -> str:

    slug = (
        clean_text(
            article.get(
                "slug",
                "",
            )
        )
        .lower()
    )

    if not slug:
        raise ValueError(
            "slugがありません。"
        )

    return slug


def get_tags(
    article: dict[str, Any],
) -> list[str]:

    raw_tags = (
        article.get(
            "tags",
            [],
        )
    )

    if not isinstance(
        raw_tags,
        list,
    ):
        return []

    return [
        clean_text(
            tag
        )
        for tag in raw_tags
        if clean_text(
            tag
        )
    ]


# =========================================================
# Category badge
# =========================================================

def draw_category_badge(
    draw: ImageDraw.ImageDraw,
    category: str,
    box: tuple[
        int,
        int,
        int,
        int,
    ],
    font_size: int,
) -> None:

    draw.rounded_rectangle(
        box,
        radius=int(
            (
                box[3]
                - box[1]
            )
            / 2
        ),
        fill=BLUE,
    )

    badge_font = font(
        font_size
    )

    bbox = draw.textbbox(
        (
            0,
            0,
        ),
        category,
        font=badge_font,
    )

    text_w = (
        bbox[2]
        - bbox[0]
    )

    text_h = (
        bbox[3]
        - bbox[1]
    )

    x = (
        box[0]
        + (
            box[2]
            - box[0]
            - text_w
        )
        / 2
    )

    y = (
        box[1]
        + (
            box[3]
            - box[1]
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
        category,
        font=badge_font,
        fill=WHITE,
    )


# =========================================================
# Feature chips
# =========================================================

def build_feature_labels(
    article: dict[str, Any],
) -> list[str]:

    tags = get_tags(
        article
    )

    category = get_category(
        article
    )

    candidates: list[str] = []

    keyword_map = {
        "料金": "料金・プラン",
        "価格": "料金・プラン",
        "比較": "比較・解説",
        "初心者": "初心者向け",
        "使い方": "使い方",
        "制限": "利用制限",
        "画像": "画像生成",
        "文章": "文章作成",
        "翻訳": "翻訳",
        "議事録": "議事録",
        "コード": "コード生成",
        "検索": "AI検索",
    }

    source_text = (
        get_title(
            article
        )
        + " "
        + get_description(
            article
        )
    )

    for keyword, label in (
        keyword_map.items()
    ):

        if (
            keyword
            in source_text
            and label
            not in candidates
        ):
            candidates.append(
                label
            )

    for tag in tags:

        if (
            tag
            not in candidates
            and len(tag) <= 8
        ):
            candidates.append(
                tag
            )

    if (
        category
        and category
        not in candidates
    ):
        candidates.append(
            category
        )

    defaults = [
        "初心者向け",
        "比較・解説",
        "最新情報",
    ]

    for label in defaults:
        if (
            label
            not in candidates
        ):
            candidates.append(
                label
            )

    return (
        candidates[:3]
    )


def draw_feature_chips(
    draw: ImageDraw.ImageDraw,
    labels: list[str],
    y: int,
) -> None:

    chip_width = 280
    chip_height = 68

    gap = 40

    total_width = (
        chip_width
        * len(labels)
        + gap
        * (
            len(labels)
            - 1
        )
    )

    start_x = int(
        (
            INSTAGRAM_WIDTH
            - total_width
        )
        / 2
    )

    for index, label in enumerate(
        labels
    ):

        x = (
            start_x
            + index
            * (
                chip_width
                + gap
            )
        )

        box = (
            x,
            y,
            x + chip_width,
            y + chip_height,
        )

        draw.rounded_rectangle(
            box,
            radius=34,
            fill=NAVY,
            outline=LIGHT_BLUE,
            width=3,
        )

        chip_font = font(
            23
        )

        bbox = draw.textbbox(
            (
                0,
                0,
            ),
            label,
            font=chip_font,
        )

        text_w = (
            bbox[2]
            - bbox[0]
        )

        text_h = (
            bbox[3]
            - bbox[1]
        )

        draw.text(
            (
                x
                + (
                    chip_width
                    - text_w
                )
                / 2,
                y
                + (
                    chip_height
                    - text_h
                )
                / 2
                - bbox[1],
            ),
            label,
            font=chip_font,
            fill=WHITE,
        )


# =========================================================
# Blog 16:9
# =========================================================

def create_blog_image(
    article: dict[str, Any],
    output_path: Path | None = None,
) -> Path:

    title = get_title(
        article
    )

    description = (
        get_description(
            article
        )
    )

    category = (
        get_category(
            article
        )
    )

    slug = get_slug(
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

    # -----------------------------------------------------
    # Brand
    # -----------------------------------------------------

    draw_brand(
        draw=draw,
        x=75,
        y=45,
        logo_size=56,
        tagline_size=21,
    )

    # -----------------------------------------------------
    # Main card
    # -----------------------------------------------------

    card = (
        65,
        190,
        1470,
        720,
    )

    draw.rounded_rectangle(
        card,
        radius=38,
        fill=WHITE,
        outline=CARD_BORDER,
        width=2,
    )

    draw_soft_decorations(
        draw=draw,
        width=BLOG_WIDTH,
        height=BLOG_HEIGHT,
    )

    # -----------------------------------------------------
    # Category
    # -----------------------------------------------------

    draw_category_badge(
        draw=draw,
        category=category,
        box=(
            105,
            225,
            400,
            285,
        ),
        font_size=26,
    )

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    title_font, lines = (
        fit_text_block(
            draw=draw,
            text=title,
            max_width=1060,
            max_lines=3,
            start_size=72,
            min_size=46,
        )
    )

    title_bottom = (
        draw_text_lines(
            draw=draw,
            lines=lines,
            x=105,
            y=335,
            text_font=title_font,
            fill=BLACK,
            line_spacing=1.22,
            final_line_blue=True,
        )
    )

    # -----------------------------------------------------
    # Divider
    # -----------------------------------------------------

    divider_y = min(
        title_bottom + 22,
        610,
    )

    draw.line(
        (
            105,
            divider_y,
            760,
            divider_y,
        ),
        fill=DIVIDER,
        width=2,
    )

    # -----------------------------------------------------
    # Description
    # -----------------------------------------------------

    if description:

        description_font = font(
            25
        )

        desc_lines = (
            wrap_japanese_text(
                draw=draw,
                text=description,
                text_font=description_font,
                max_width=990,
                max_lines=2,
                add_ellipsis=True,
            )
        )

        draw_text_lines(
            draw=draw,
            lines=desc_lines,
            x=105,
            y=divider_y + 26,
            text_font=description_font,
            fill=TEXT_MUTED,
            line_spacing=1.45,
        )

    # -----------------------------------------------------
    # Footer wave
    # -----------------------------------------------------

    draw_wave(
        draw=draw,
        width=BLOG_WIDTH,
        base_y=705,
        amplitude=34,
        wave_height=160,
    )

    draw.text(
        (
            78,
            782,
        ),
        "ALSIVO.COM",
        font=font(
            24
        ),
        fill=MUTED,
    )

    image.save(
        output_path,
        format="PNG",
        optimize=True,
    )

    return output_path


# =========================================================
# Instagram 4:5
# =========================================================

def create_instagram_image(
    article: dict[str, Any],
    output_path: Path | None = None,
) -> Path:

    title = get_title(
        article
    )

    description = (
        get_description(
            article
        )
    )

    category = (
        get_category(
            article
        )
    )

    slug = get_slug(
        article
    )

    labels = (
        build_feature_labels(
            article
        )
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

    # -----------------------------------------------------
    # Brand
    # -----------------------------------------------------

    draw_brand(
        draw=draw,
        x=55,
        y=38,
        logo_size=54,
        tagline_size=20,
    )

    # -----------------------------------------------------
    # Card
    #
    # Category badgeとの重なりを防ぐため、
    # badgeはcard内に配置する。
    # -----------------------------------------------------

    card = (
        45,
        185,
        1035,
        1010,
    )

    draw.rounded_rectangle(
        card,
        radius=36,
        fill=WHITE,
        outline=CARD_BORDER,
        width=2,
    )

    # -----------------------------------------------------
    # Category badge
    # -----------------------------------------------------

    draw_category_badge(
        draw=draw,
        category=category,
        box=(
            85,
            225,
            390,
            295,
        ),
        font_size=28,
    )

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    title_font, lines = (
        fit_text_block(
            draw=draw,
            text=title,
            max_width=850,
            max_lines=4,
            start_size=76,
            min_size=48,
        )
    )

    title_bottom = (
        draw_text_lines(
            draw=draw,
            lines=lines,
            x=85,
            y=350,
            text_font=title_font,
            fill=BLACK,
            line_spacing=1.24,
            final_line_blue=True,
        )
    )

    # -----------------------------------------------------
    # Divider
    # -----------------------------------------------------

    divider_y = min(
        title_bottom + 25,
        750,
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

    # -----------------------------------------------------
    # Description
    # -----------------------------------------------------

    if description:

        description_font = font(
            27
        )

        desc_lines = (
            wrap_japanese_text(
                draw=draw,
                text=description,
                text_font=description_font,
                max_width=850,
                max_lines=3,
                add_ellipsis=True,
            )
        )

        draw_text_lines(
            draw=draw,
            lines=desc_lines,
            x=85,
            y=divider_y + 32,
            text_font=description_font,
            fill=BLACK,
            line_spacing=1.45,
        )

    # -----------------------------------------------------
    # Chips
    # -----------------------------------------------------

    draw_feature_chips(
        draw=draw,
        labels=labels,
        y=1065,
    )

    # -----------------------------------------------------
    # Background waves
    # -----------------------------------------------------

    draw_wave(
        draw=draw,
        width=INSTAGRAM_WIDTH,
        base_y=1055,
        amplitude=35,
        wave_height=240,
    )

    # chipsを波の上に再描画
    draw_feature_chips(
        draw=draw,
        labels=labels,
        y=1065,
    )

    # -----------------------------------------------------
    # CTA
    # -----------------------------------------------------

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

    cta_font = font(
        24
    )

    draw.text(
        (
            80,
            1249,
        ),
        "詳しくはプロフィールのリンクからチェック！",
        font=cta_font,
        fill=WHITE,
    )

    draw.text(
        (
            830,
            1250,
        ),
        "ALSIVO.COM",
        font=font(
            21
        ),
        fill=WHITE,
    )

    image.save(
        output_path,
        format="PNG",
        optimize=True,
    )

    return output_path


# =========================================================
# Combined
# =========================================================

def generate_alsivo_images(
    article: dict[str, Any],
) -> dict[str, Path]:

    blog_path = (
        create_blog_image(
            article
        )
    )

    instagram_path = (
        create_instagram_image(
            article
        )
    )

    return {
        "blog": blog_path,
        "instagram": instagram_path,
    }