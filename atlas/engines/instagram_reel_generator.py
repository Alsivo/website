"""Instagram投稿画像とローカルBGMから7秒のリール動画を作る。"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import imageio_ffmpeg


ATLAS_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ATLAS_DIR.parent
SOCIAL_IMAGE_DIR = PROJECT_ROOT / "public" / "images" / "social"
BGM_FILE = ATLAS_DIR / "local_assets" / "audio" / "investor_night.mp3"
DURATION_SECONDS = 7


def reel_path(slug: str) -> Path:
    return SOCIAL_IMAGE_DIR / f"{slug}-instagram-reel.mp4"


def generate_reel(slug: str) -> Path:
    """1080x1920・上下黒・BGM付きの7秒MP4を生成する。"""
    if not slug or any(value in slug for value in ("/", "\\", "..")):
        raise ValueError("安全な記事IDを指定してください。")
    image = SOCIAL_IMAGE_DIR / f"{slug}-instagram.png"
    if not image.is_file():
        raise FileNotFoundError(f"Instagram投稿画像がありません: {image}")
    if not BGM_FILE.is_file():
        raise FileNotFoundError(f"リール用BGMがありません: {BGM_FILE}")

    output = reel_path(slug)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".tmp.mp4")
    temporary.unlink(missing_ok=True)
    filters = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[image];"
        "color=c=black:s=1080x1920:r=30:d=7[background];"
        "[background][image]overlay=(W-w)/2:(H-h)/2:shortest=1,"
        "fade=t=in:st=0:d=0.3,fade=t=out:st=6.3:d=0.7[video];"
        "[1:a]atrim=start=0:end=7,asetpts=PTS-STARTPTS,"
        "afade=t=in:st=0:d=0.3,afade=t=out:st=6.3:d=0.7,"
        "volume=0.30[audio]"
    )
    command = [
        imageio_ffmpeg.get_ffmpeg_exe(), "-y",
        "-loop", "1", "-i", str(image), "-i", str(BGM_FILE),
        "-filter_complex", filters,
        "-map", "[video]", "-map", "[audio]", "-t", str(DURATION_SECONDS),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-ar", "48000", "-movflags", "+faststart", str(temporary),
    ]
    result = subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8",
        errors="replace", check=False,
    )
    if result.returncode != 0 or not temporary.is_file():
        temporary.unlink(missing_ok=True)
        raise RuntimeError("リール動画の生成に失敗しました。\n" + result.stderr[-2000:])
    temporary.replace(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description="ALSIVO Instagram Reel Generator")
    parser.add_argument("article_slug")
    args = parser.parse_args()
    print(f"7秒リール動画を生成しました: {generate_reel(args.article_slug.strip())}")


if __name__ == "__main__":
    main()
