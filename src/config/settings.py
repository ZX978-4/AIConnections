# src/config/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# --- 认证配置 ---
HF_TOKEN = os.getenv("HF_TOKEN")

# --- 路径配置 ---
# 获取项目根目录 (假设 settings.py 在 src/config/ 下)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 数据目录
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# 输出目录
OUTPUT_DIR = BASE_DIR / "output"
GRAPHS_DIR = OUTPUT_DIR / "graphs"
IMAGES_DIR = OUTPUT_DIR / "images"
HTML_DIR = OUTPUT_DIR / "html"

# --- 爬虫与解析配置 ---
# 默认抓取的 Top N 模型数量
TOP_K_MODELS = 1000
# Hugging Face API Base URL (如有需要直接用 requests 时使用)
HF_API_BASE = "https://huggingface.co/api"

# 确保所有目录存在
def ensure_directories():
    directories = [
        RAW_DATA_DIR, PROCESSED_DATA_DIR,
        GRAPHS_DIR, IMAGES_DIR, HTML_DIR
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

# 初始化时自动创建文件夹
ensure_directories()