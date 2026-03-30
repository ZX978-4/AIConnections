# src/config/settings.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
HF_TOKEN = os.getenv("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")

# ===================== 爬取配置 =====================
TOP_MODELS_LIMIT = 1000  # 爬取前1000热门模型
BATCH_SIZE = 100         # 分页大小
SLEEP_INTERVAL = 5       # 每50个模型暂停5秒，防限流

# ===================== 文件路径配置 =====================
# 根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 数据目录
DATA_RAW = os.path.join(BASE_DIR, "../data/raw")
DATA_PROCESSED = os.path.join(BASE_DIR, "../data/processed")
# 输出目录
OUTPUT_GRAPHS = os.path.join(BASE_DIR, "../output/graphs")
OUTPUT_IMAGES = os.path.join(BASE_DIR, "../output/images")
OUTPUT_HTML = os.path.join(BASE_DIR, "../output/html")

# 自动创建文件夹
for path in [DATA_RAW, DATA_PROCESSED, OUTPUT_GRAPHS, OUTPUT_IMAGES, OUTPUT_HTML]:
    os.makedirs(path, exist_ok=True)

# ===================== 正则匹配规则（解析Model Card用） =====================
import regex as re
PATTERN_BASE_MODEL = re.compile(r"(base model|finetuned on|pretrained on)\s*[:=]?\s*([\w\-/]+)", re.IGNORECASE)
PATTERN_TRAIN_DATA = re.compile(r"(trained on|training data|dataset)\s*[:=]?\s*([\w\-/]+)", re.IGNORECASE)
PATTERN_FT_DATA = re.compile(r"(finetuned on|ft data|微调数据)\s*[:=]?\s*([\w\-/]+)", re.IGNORECASE)

# ===================== 统一保存路径 =====================
SAVE_PATHS = {
    "raw": DATA_RAW,
    "processed": DATA_PROCESSED,
    "graphs": OUTPUT_GRAPHS,
    "images": OUTPUT_IMAGES,
    "html": OUTPUT_HTML,
    "output": os.path.join(BASE_DIR, "../output")
}