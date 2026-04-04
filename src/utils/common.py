# src/utils/common.py
import logging
import sys
from pathlib import Path
import json
import ast

def setup_logger(name="hf_supply_chain"):
    """配置并返回一个标准的日志记录器"""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # 控制台输出格式
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


logger = setup_logger()


def save_json(data, filepath: Path):
    """将数据保存为 JSON 文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    logger.info(f"Data successfully saved to {filepath}")


def load_json(filepath: Path):
    """从 JSON 文件加载数据"""
    if not filepath.exists():
        logger.warning(f"File {filepath} does not exist.")
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def clean_license(license_data):
    """规范化证书格式，确保输出为统一的字符串"""
    if not license_data or license_data == "unknown":
        return "unknown"

    # 1. 处理被误作为字符串的列表，例如 "['mit', 'apache-2.0']"
    if isinstance(license_data, str) and license_data.startswith("["):
        try:
            license_data = ast.literal_eval(license_data)
        except Exception:
            pass

    # 2. 如果是列表格式，将其合并为逗号分隔的字符串
    if isinstance(license_data, list):
        # 过滤掉空值并转小写
        parts = [str(x).strip().lower() for x in license_data if x]
        return ", ".join(parts) if parts else "unknown"

    # 3. 如果是普通字符串，直接处理
    return str(license_data).strip().lower()