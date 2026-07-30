from pathlib import Path
from slugify import slugify

from config import CONTENT_DIR


def save_article(title: str, article: str):

    slug = slugify(title)

    filepath = CONTENT_DIR / f"{slug}.mdx"

    mdx = f"""---
title: "{title}"
description: ""
date: "2026-07-30"
category: "AI"
tags:
  - "AI"
readingTime: "5 min"
published: true
---

{article}
"""

    filepath.write_text(
        mdx,
        encoding="utf-8"
    )

    return filepath