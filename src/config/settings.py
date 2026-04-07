# src/config/settings.py
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

OUTPUT_DIR = BASE_DIR / "output"
GRAPHS_DIR = OUTPUT_DIR / "graphs"
IMAGES_DIR = OUTPUT_DIR / "images"
HTML_DIR = OUTPUT_DIR / "html"

TOP_K_MODELS = 1000
HF_API_BASE = "https://huggingface.co/api"


def ensure_directories():
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        GRAPHS_DIR,
        IMAGES_DIR,
        HTML_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


ensure_directories()
