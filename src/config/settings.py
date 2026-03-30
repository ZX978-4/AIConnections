# src/config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

TOP_MODELS_LIMIT = 1000
BATCH_SIZE = 50
SLEEP_INTERVAL = 10

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATA_RAW = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "data", "processed")
OUTPUT_GRAPHS = os.path.join(BASE_DIR, "output", "graphs")
OUTPUT_IMAGES = os.path.join(BASE_DIR, "output", "images")
OUTPUT_HTML = os.path.join(BASE_DIR, "output", "html")

for path in [DATA_RAW, DATA_PROCESSED, OUTPUT_GRAPHS, OUTPUT_IMAGES, OUTPUT_HTML]:
    os.makedirs(path, exist_ok=True)

import re
PATTERN_BASE_MODEL = re.compile(r"(base model|finetuned on|pretrained on)\s*[:=]?\s*([\w\-/]+)", re.I)
PATTERN_TRAIN_DATA = re.compile(r"(trained on|training data|dataset)\s*[:=]?\s*([\w\-/]+)", re.I)
PATTERN_FT_DATA = re.compile(r"(finetuned on|ft data|微调数据)\s*[:=]?\s*([\w\-/]+)", re.I)

SAVE_PATHS = {
    "raw": DATA_RAW,
    "processed": DATA_PROCESSED,
    "graphs": OUTPUT_GRAPHS,
    "images": OUTPUT_IMAGES,
    "html": OUTPUT_HTML,
    "output": os.path.join(BASE_DIR, "output")
}