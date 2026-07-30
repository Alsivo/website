from pathlib import Path
from slugify import slugify
from datetime import date


BLOG_DIR = Path("../content/blog")


def publish_article(article: dict):

    slug = slugify(article["title"])

    filepath = BLOG_DIR / f"{slug}.mdx"

    mdx = f"""---
title: "{article["title"]}"
description: "{article["description"]}"
date: "{date.today()}"
category: "{article["category"]}"
tags:
"""

    for tag in article["tags"]:
        mdx += f'  - "{tag}"\n'

    mdx += """
readingTime: "5 min"
published: true
---

"""

    mdx += article["content"]

    filepath.write_text(
        mdx,
        encoding="utf-8"
    )

    return filepath