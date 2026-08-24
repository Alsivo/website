"""デプロイ完了を待ってからSNS配信へ進む。"""

from __future__ import annotations

import argparse
import time

import requests


SITE_URL = "https://www.alsivo.com"


def wait_until_public(slug: str, timeout_seconds: int = 300) -> bool:
    urls = [
        f"{SITE_URL}/blog/{slug}",
        f"{SITE_URL}/images/social/{slug}-instagram.png",
        f"{SITE_URL}/images/social/{slug}-instagram-reel.mp4",
    ]
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        ready = True
        for url in urls:
            try:
                response = requests.get(url, timeout=15)
                if response.status_code != 200:
                    ready = False
                    break
            except requests.RequestException:
                ready = False
                break
        if ready:
            return True
        time.sleep(10)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="ALSIVOのデプロイ完了を待ちます。")
    parser.add_argument("slug")
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    if not wait_until_public(args.slug.strip(), max(10, args.timeout)):
        raise SystemExit("本番反映を確認できませんでした。SNS配信は次回運転へ繰り越します。")
    print("記事とInstagram画像の本番反映を確認しました。")


if __name__ == "__main__":
    main()
