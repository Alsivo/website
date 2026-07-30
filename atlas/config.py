from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

CONTENT_DIR = ROOT / "content" / "blog"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

MODEL = "gpt-5"