from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageOps,
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
    WEBSITE_ROOT
    / "public"
    / "images"
    / "social"
)

CHARACTER_DIR = WEBSITE_ROOT / "public" / "images" / "characters"
ARTICLE_BACKGROUND_DIR = WEBSITE_ROOT / "public" / "images" / "article-backgrounds"


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

    text = (
        text
        .replace(
            "\r",
            " ",
        )
        .replace(
            "\n",
            " ",
        )
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


def compact_text(
    value: str,
) -> str:
    """
    改行結果検証用。

    半角・全角を含む空白と改行だけ除去し、
    文章自体が変更されていないことを確認する。
    """

    return re.sub(
        r"\s+",
        "",
        str(value),
    )


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
#
# AI改行が使えない場合だけ使用する。
# =========================================================

def find_break_index(
    draw: ImageDraw.ImageDraw,
    text: str,
    text_font: ImageFont.FreeTypeFont,
    max_width: int,
) -> int:
    """
    幅を超えない範囲で改行位置を探す。

    AI改行が取得できない場合の
    フォールバックとして使用する。
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
    # 自然な区切り位置を優先
    # -----------------------------------------------------

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
    """
    機械的な文字移動は行わない。

    以前は最終行が短い場合に、
    前行末尾から2〜4文字を強制的に移動していたが、
    英単語や日本語の語句を途中で分断する原因になるため廃止。

    行バランスはAI改行を優先し、
    フォールバック時も安全な改行位置だけで処理する。
    """

    return lines


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

    lines: list[str] = []

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

        line = (
            rest[
                :break_index
            ]
            .strip()
        )

        rest = (
            rest[
                break_index:
            ]
            .strip()
        )

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
# AI line helpers
# =========================================================

def get_ai_lines(
    article: dict[str, Any],
    key: str,
) -> list[str]:
    """AIが生成した改行済み文字列を取得する。"""

    raw_lines = article.get(
        key,
        [],
    )

    if not isinstance(
        raw_lines,
        list,
    ):

        return []

    lines: list[str] = []

    for raw_line in raw_lines:

        line = clean_text(
            raw_line
        )

        if line:

            lines.append(
                line
            )

    return lines


def validate_ai_lines(
    original_text: str,
    lines: list[str],
) -> bool:
    """
    AIが文章を書き換えていないか確認する。

    行を連結して元文章と同一ならTrue。
    """

    if not lines:
        return False

    original = compact_text(
        clean_text(
            original_text
        )
    )

    reconstructed = compact_text(
        "".join(
            lines
        )
    )

    return (
        original
        == reconstructed
    )


# =========================================================
# AI title layout helpers
# =========================================================

def split_long_title_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    max_width: int,
    max_lines: int,
    check_font_size: int,
) -> list[str]:
    """
    AIタイトル改行を維持しつつ、
    長すぎる行だけ追加分割する。
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

        if available_slots <= 1:

            result.append(
                line
            )

            continue

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

            if slots_left <= 1:

                result.append(
                    rest
                )

                break

            break_index = (
                find_break_index(
                    draw=draw,
                    text=rest,
                    text_font=check_font,
                    max_width=max_width,
                )
            )

            if (
                break_index <= 0
                or break_index
                >= len(rest)
            ):

                result.append(
                    rest
                )

                break

            first = (
                rest[
                    :break_index
                ]
                .strip()
            )

            second = (
                rest[
                    break_index:
                ]
                .strip()
            )

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


def fit_prebroken_title(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    max_width: int,
    max_font_size: int,
    min_font_size: int,
) -> ImageFont.FreeTypeFont:
    """
    AIが決めたタイトル改行を維持し、
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
    """AIタイトル改行が使えない場合のフォールバック。"""

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

        reconstructed = compact_text(
            "".join(
                lines
            )
        )

        original = compact_text(
            cleaned_title
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

BLOG_TITLE_FONT_SIZE = 88
INSTAGRAM_TITLE_FONT_SIZE = 74

BLOG_TITLE_LINE_GAP = 12
INSTAGRAM_TITLE_LINE_GAP = 14


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
    AIが決めた自然な改行を最優先する。

    1. AI改行をそのまま使用できるか確認
    2. 改行位置を変えず、フォントサイズだけ縮小
    3. min_font_sizeでも入らない場合のみ追加分割
    4. それでも無理な場合だけ通常フォールバック

    Blog / Instagramでは
    max_width・font sizeが別々に渡されるため、
    それぞれ独立したレイアウトになる。
    """

    ai_lines = get_ai_lines(
        article,
        ai_key,
    )

    if (
        ai_lines
        and len(ai_lines) <= max_lines
        and validate_ai_lines(
            title,
            ai_lines,
        )
    ):

        # -----------------------------------------------------
        # 最優先：
        # AIの自然な改行を一切変更せず、
        # フォントサイズだけ下げて収める
        # -----------------------------------------------------

        for size in range(
            max_font_size,
            min_font_size - 1,
            -2,
        ):
            title_font = font(
                size
            )

            if all(
                text_width(
                    draw,
                    line,
                    title_font,
                )
                <= max_width
                for line in ai_lines
            ):
                return (
                    title_font,
                    ai_lines,
                )

        # -----------------------------------------------------
        # minサイズでも入らない場合だけ
        # AI行を追加分割する
        #
        # ここではmin_font_sizeを基準にする。
        # -----------------------------------------------------

        adjusted_lines = (
            split_long_title_lines(
                draw=draw,
                lines=ai_lines,
                max_width=max_width,
                max_lines=max_lines,
                check_font_size=min_font_size,
            )
        )

        if (
            adjusted_lines
            and len(adjusted_lines)
            <= max_lines
            and validate_ai_lines(
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

    # ---------------------------------------------------------
    # AI結果そのものが使えなかった場合だけ
    # 機械フォールバック
    # ---------------------------------------------------------

    return fallback_title_lines(
        draw=draw,
        title=title,
        max_width=max_width,
        max_lines=max_lines,
        max_font_size=max_font_size,
        min_font_size=min_font_size,
    )


# =========================================================
# AI subtitle layout helpers
# =========================================================

def fit_prebroken_subtitle(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    max_width: int,
    max_font_size: int,
    min_font_size: int,
) -> ImageFont.FreeTypeFont:
    """
    AIが決めた説明文の改行を維持し、
    全行が横幅へ収まる最大フォントサイズを探す。
    """

    for size in range(
        max_font_size,
        min_font_size - 1,
        -2,
    ):

        subtitle_font = font(
            size
        )

        if all(
            text_width(
                draw,
                line,
                subtitle_font,
            )
            <= max_width
            for line in lines
        ):

            return subtitle_font

    return font(
        min_font_size
    )


def subtitle_block_height(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    subtitle_font: ImageFont.FreeTypeFont,
    line_gap: int,
) -> int:
    """説明文ブロック全体の高さを計算する。"""

    if not lines:
        return 0

    height = 0

    for index, line in enumerate(
        lines
    ):

        height += text_height(
            draw,
            line,
            subtitle_font,
        )

        if index < len(lines) - 1:
            height += line_gap

    return height


def prepare_subtitle(
    draw: ImageDraw.ImageDraw,
    article: dict[str, Any],
    subtitle: str,
    ai_key: str,
    max_width: int,
    max_lines: int,
    max_font_size: int,
    min_font_size: int,
    max_height: int,
    line_gap: int,
) -> tuple[
    ImageFont.FreeTypeFont,
    list[str],
]:
    """
    説明文の改行を決定する。

    1. Blog/Instagram専用のAI改行を最優先
    2. AIが文章を書き換えていないか検証
    3. 横幅と高さに合わせてフォントを調整
    4. AI結果が使えない場合だけ機械改行へフォールバック

    BlogとInstagramではai_keyが異なるため、
    それぞれ独立した改行結果を使用できる。
    """

    cleaned_subtitle = clean_text(
        subtitle
    )

    if not cleaned_subtitle:

        return (
            font(
                max_font_size
            ),
            [],
        )

    ai_lines = get_ai_lines(
        article,
        ai_key,
    )

    # -----------------------------------------------------
    # AI改行を使用
    # -----------------------------------------------------

    if (
        ai_lines
        and len(ai_lines)
        <= max_lines
        and validate_ai_lines(
            cleaned_subtitle,
            ai_lines,
        )
    ):

        for size in range(
            max_font_size,
            min_font_size - 1,
            -2,
        ):

            subtitle_font = font(
                size
            )

            width_ok = all(
                text_width(
                    draw,
                    line,
                    subtitle_font,
                )
                <= max_width
                for line in ai_lines
            )

            if not width_ok:
                continue

            block_height = (
                subtitle_block_height(
                    draw=draw,
                    lines=ai_lines,
                    subtitle_font=subtitle_font,
                    line_gap=line_gap,
                )
            )

            if block_height <= max_height:

                return (
                    subtitle_font,
                    ai_lines,
                )

    # -----------------------------------------------------
    # Fallback
    #
    # AI改行がない場合だけ、
    # 画像幅を見ながら機械的に処理する。
    # -----------------------------------------------------

    for size in range(
        max_font_size,
        min_font_size - 1,
        -2,
    ):

        subtitle_font = font(
            size
        )

        lines = wrap_text(
            draw=draw,
            text=cleaned_subtitle,
            text_font=subtitle_font,
            max_width=max_width,
            max_lines=max_lines,
            ellipsis=False,
        )

        if not validate_ai_lines(
            cleaned_subtitle,
            lines,
        ):

            continue

        block_height = (
            subtitle_block_height(
                draw=draw,
                lines=lines,
                subtitle_font=subtitle_font,
                line_gap=line_gap,
            )
        )

        if block_height <= max_height:

            return (
                subtitle_font,
                lines,
            )

    # -----------------------------------------------------
    # 最終フォールバック
    #
    # ここでは勝手に文章を切らない。
    # minサイズで最大行数まで返す。
    # それでも入らない場合は、
    # generate_images.py側でAI再要約する対象になる。
    # -----------------------------------------------------

    final_font = font(
        min_font_size
    )

    final_lines = wrap_text(
        draw=draw,
        text=cleaned_subtitle,
        text_font=final_font,
        max_width=max_width,
        max_lines=max_lines,
        ellipsis=False,
    )

    return (
        final_font,
        final_lines,
    )


# =========================================================
# Visual helpers
# =========================================================

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

    tagline_size = 38

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

    tags: list[str] = []

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


def get_image_title(
    article: dict[str, Any],
) -> str:
    """画像専用タイトルを取得する。"""

    image_title = clean_text(
        article.get(
            "image_title",
            "",
        )
    )

    if image_title:
        return image_title

    return clean_text(
        article.get(
            "title",
            "",
        )
    )


def get_image_subtitle(
    article: dict[str, Any],
) -> str:
    """画像専用サブタイトルを取得する。"""

    image_subtitle = clean_text(
        article.get(
            "image_subtitle",
            "",
        )
    )

    if image_subtitle:
        return image_subtitle

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

    if not get_image_title(
        article
    ):

        raise ValueError(
            "画像へ表示するタイトルがありません。"
        )


# =========================================================
# Character dialogue image
# =========================================================

def _wrap_characters(draw: ImageDraw.ImageDraw, text: str, text_font: Any, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for character in clean_text(text):
        candidate = current + character
        if current and draw.textbbox((0, 0), candidate, font=text_font)[2] > max_width:
            lines.append(current)
            current = character
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines[:4]


def _find_article_background(slug: str) -> Path | None:
    for suffix in (".webp", ".png", ".jpg", ".jpeg"):
        candidate = ARTICLE_BACKGROUND_DIR / f"{slug}{suffix}"
        if candidate.is_file():
            return candidate
    return None


def _create_character_dialogue_image(article: dict[str, Any], output_path: Path, width: int, height: int, instagram: bool = False) -> Path:
    background_path = _find_article_background(clean_text(article.get("slug", "")))
    if background_path is not None:
        background = Image.open(background_path).convert("RGB")
        image = ImageOps.fit(background, (width, height), method=Image.Resampling.LANCZOS).convert("RGBA")
        image.alpha_composite(Image.new("RGBA", (width, height), (240, 247, 250, 105)))
    else:
        image = Image.new("RGBA", (width, height), (238, 247, 251, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((32, 32, width - 32, height - 32), radius=42, outline=(255, 255, 255), width=3)
    if instagram:
        draw.text((58, 48), "ALSIVO", font=font(34), fill=NAVY)
        if bool(article.get("is_affiliate_article", False)):
            draw.text((width - 145, 48), "#PR", font=font(32), fill=NAVY)
    al = Image.open(CHARACTER_DIR / "al-upper-body-v1.png").convert("RGBA")
    cibo = Image.open(CHARACTER_DIR / "cibo-upper-body-v1.png").convert("RGBA")
    character_height = int(height * (0.36 if instagram else 0.42))
    for portrait in (al, cibo):
        portrait.thumbnail((int(width * .34), character_height), Image.Resampling.LANCZOS)
    al_position = (42, int(height * .05))
    cibo_position = (width - cibo.width - 42, height - cibo.height - 38)
    image.alpha_composite(al, al_position)
    image.alpha_composite(cibo, cibo_position)
    upper = (al_position[0] + al.width - 14, int(height * .08), width - 52, int(height * .44))
    lower = (52, int(height * .50), cibo_position[0] + 14, int(height * .91))
    longest_copy = max(len(get_image_title(article)), len(get_image_subtitle(article)))
    if instagram:
        common_copy_size = 38 if longest_copy <= 38 else 34 if longest_copy <= 65 else 30
    else:
        common_copy_size = 40 if longest_copy <= 38 else 36 if longest_copy <= 65 else 32
    common_copy_font = font(common_copy_size)
    for box, side, copy, copy_font, fill in (
        (upper, "left", get_image_title(article), common_copy_font, (248, 252, 255, 242)),
        (lower, "right", get_image_subtitle(article), common_copy_font, (238, 249, 251, 242)),
    ):
        draw.rounded_rectangle(box, radius=28, fill=fill, outline=BORDER, width=3)
        middle_y = int((box[1] + box[3]) / 2)
        if side == "left":
            draw.polygon([(box[0], middle_y - 18), (box[0] - 30, middle_y), (box[0], middle_y + 18)], fill=fill, outline=BORDER)
        else:
            draw.polygon([(box[2], middle_y - 18), (box[2] + 30, middle_y), (box[2], middle_y + 18)], fill=fill, outline=BORDER)
        lines = _wrap_characters(draw, copy, copy_font, box[2] - box[0] - 48)
        line_box = draw.multiline_textbbox((0, 0), "\n".join(lines), font=copy_font, spacing=10)
        text_height = line_box[3] - line_box[1]
        draw.multiline_text((box[0] + 24, box[1] + max(20, (box[3] - box[1] - text_height) // 2)), "\n".join(lines), font=copy_font, fill=NAVY, spacing=10)
    image.convert("RGB").save(output_path, format="PNG", optimize=True)
    return output_path


# =========================================================
# Blog 16:9
# =========================================================

def create_blog_image(
    article: dict[str, Any],
    output_path: Path | None = None,
) -> Path:
    """Blog用16:9画像を生成する。"""

    validate_article(
        article
    )

    slug = clean_text(
        article["slug"]
    )

    title = get_image_title(
        article
    )

    subtitle = get_image_subtitle(
        article
    )

    category = get_category(
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

    return _create_character_dialogue_image(
        article, output_path, BLOG_WIDTH, BLOG_HEIGHT
    )

    draw_gradient(
        image
    )

    draw = ImageDraw.Draw(
        image
    )

    # -----------------------------------------------------
    # Card
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Category
    # -----------------------------------------------------

    badge = (
        110,
        118,
        410,
        184,
    )

    draw_badge(
        draw,
        badge,
        category,
    )

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    title_x = 110
    title_y = 225

    title_max_width = (
        BLOG_WIDTH
        - title_x
        - 120
    )

    title_font, title_lines = (
        prepare_title(
            draw=draw,
            article=article,
            title=title,
            ai_key="blog_title_lines",
            max_width=title_max_width,
            max_lines=3,
            max_font_size=BLOG_TITLE_FONT_SIZE,
            min_font_size=60,
        )
    )

    current_y = title_y

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
            + BLOG_TITLE_LINE_GAP
        )

    # -----------------------------------------------------
    # Divider
    # -----------------------------------------------------

    divider_y = (
        current_y + 28
    )

    divider_y = min(
        divider_y,
        560,
    )

    draw.line(
        (
            title_x,
            divider_y,
            BLOG_WIDTH - 190,
            divider_y,
        ),
        fill=DIVIDER,
        width=2,
    )

    # -----------------------------------------------------
    # Subtitle
    #
    # Blog専用のAI改行
    # blog_subtitle_linesを最優先する。
    # -----------------------------------------------------

    if subtitle:

        subtitle_y = (
            divider_y + 30
        )

        subtitle_max_height = (
            738
            - subtitle_y
        )

        subtitle_font, subtitle_lines = (
            prepare_subtitle(
                draw=draw,
                article=article,
                subtitle=subtitle,
                ai_key="blog_subtitle_lines",
                max_width=1220,
                max_lines=4,
                max_font_size=64,
                min_font_size=48,
                max_height=subtitle_max_height,
                line_gap=12,
            )
        )

        current_subtitle_y = subtitle_y

        for line in subtitle_lines:

            draw.text(
                (
                    title_x,
                    current_subtitle_y,
                ),
                line,
                font=subtitle_font,
                fill=TEXT_MUTED,
            )

            current_subtitle_y += (
                text_height(
                    draw,
                    line,
                    subtitle_font,
                )
                + 12
            )

    # -----------------------------------------------------
    # Decoration
    # -----------------------------------------------------

    draw_wave(
        draw=draw,
        width=BLOG_WIDTH,
        base_y=750,
        amplitude=24,
        height=110,
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
    """Instagram用4:5画像を生成する。"""

    validate_article(
        article
    )

    slug = clean_text(
        article["slug"]
    )

    title = get_image_title(
        article
    )

    subtitle = get_image_subtitle(
        article
    )

    category = get_category(
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

    return _create_character_dialogue_image(
        article, output_path, INSTAGRAM_WIDTH, INSTAGRAM_HEIGHT, instagram=True
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
        draw,
        56,
        26,
        large=False,
    )

    if bool(article.get("is_affiliate_article", False)):
        pr_font = font(34)
        pr_box = (880, 38, 1015, 100)
        draw.rounded_rectangle(pr_box, radius=18, fill=WHITE)
        draw_centered_text(
            draw=draw,
            box=pr_box,
            text="#PR",
            text_font=pr_font,
            fill=NAVY,
        )

    # -----------------------------------------------------
    # Main card
    # -----------------------------------------------------

    card = (
        45,
        175,
        1035,
        1005,
    )

    draw.rounded_rectangle(
        card,
        radius=34,
        fill=WHITE,
        outline=BORDER,
        width=2,
    )

    # -----------------------------------------------------
    # Category
    # -----------------------------------------------------

    badge = (
        85,
        215,
        390,
        286,
    )

    draw_badge(
        draw,
        badge,
        category,
    )

    # -----------------------------------------------------
    # Title
    # -----------------------------------------------------

    title_x = 85
    title_y = 325

    title_max_width = (
        1035
        - title_x
        - 65
    )

    title_font, title_lines = (
        prepare_title(
            draw=draw,
            article=article,
            title=title,
            ai_key="instagram_title_lines",
            max_width=title_max_width,
            max_lines=4,
            max_font_size=INSTAGRAM_TITLE_FONT_SIZE,
            min_font_size=50,
        )
    )

    current_y = title_y

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
            + INSTAGRAM_TITLE_LINE_GAP
        )

    # -----------------------------------------------------
    # Divider
    # -----------------------------------------------------

    divider_y = (
        current_y + 26
    )

    divider_y = min(
        divider_y,
        675,
    )

    draw.line(
        (
            85,
            divider_y,
            950,
            divider_y,
        ),
        fill=DIVIDER,
        width=2,
    )

    # -----------------------------------------------------
    # Subtitle
    #
    # Instagram専用のAI改行
    # instagram_subtitle_linesを最優先する。
    #
    # Blogとは画像幅が違うため
    # 同一改行結果を使わない。
    # -----------------------------------------------------

    if subtitle:

        subtitle_y = (
            divider_y + 28
        )

        subtitle_max_height = (
            965
            - subtitle_y
        )

        subtitle_font, subtitle_lines = (
            prepare_subtitle(
                draw=draw,
                article=article,
                subtitle=subtitle,
                ai_key="instagram_subtitle_lines",
                max_width=850,
                max_lines=5,
                max_font_size=56,
                min_font_size=44,
                max_height=subtitle_max_height,
                line_gap=10,
            )
        )

        current_subtitle_y = subtitle_y

        for line in subtitle_lines:

            draw.text(
                (
                    85,
                    current_subtitle_y,
                ),
                line,
                font=subtitle_font,
                fill=BLACK,
            )

            current_subtitle_y += (
                text_height(
                    draw,
                    line,
                    subtitle_font,
                )
                + 10
            )

    # -----------------------------------------------------
    # Waves
    # -----------------------------------------------------

    draw_wave(
        draw=draw,
        width=INSTAGRAM_WIDTH,
        base_y=1020,
        amplitude=28,
        height=260,
    )

    # -----------------------------------------------------
    # Tags
    # -----------------------------------------------------

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

    chip_y1 = 1050
    chip_y2 = 1130

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
            radius=40,
            fill=NAVY,
            outline=BLUE_LIGHT,
            width=3,
        )

        chip_font = font(
            26
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

    # -----------------------------------------------------
    # CTA
    # -----------------------------------------------------

    cta_box = (
        45,
        1180,
        1035,
        1325,
    )

    draw.rounded_rectangle(
        cta_box,
        radius=62,
        fill=BLUE,
    )

    cta_text = (
        "詳しくはプロフィールのリンクからチェック！"
    )

    cta_font = font(
        32
    )

    cta_text_box = (
        65,
        1188,
        1015,
        1250,
    )

    draw_centered_text(
        draw=draw,
        box=cta_text_box,
        text=cta_text,
        text_font=cta_font,
        fill=WHITE,
    )

    website_text = (
        "alsivo.com"
    )

    website_font = font(
        32
    )

    website_box = (
        65,
        1250,
        1015,
        1317,
    )

    draw_centered_text(
        draw=draw,
        box=website_box,
        text=website_text,
        text_font=website_font,
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

    ・Blog 16:9
    ・Instagram 4:5

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
