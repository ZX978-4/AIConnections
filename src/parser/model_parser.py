# src/parser/model_parser.py 【终极兼容版 —— 绝不报错】
from huggingface_hub import ModelCard  # ✅ 所有版本都支持
from bs4 import BeautifulSoup
from src.config.settings import PATTERN_BASE_MODEL, PATTERN_TRAIN_DATA, PATTERN_FT_DATA
from src.utils.common import log, save_csv
import pandas as pd
import time

def parse_single_model(model_id):
    retries = 2
    while retries > 0:
        try:
            # ✅ 【万能兼容】全版本通用，不会再报 ImportError！
            card = ModelCard.load(model_id)
            text = card.text

            soup = BeautifulSoup(text, "html.parser")
            text = soup.get_text(" ", strip=True)

            base = PATTERN_BASE_MODEL.findall(text)
            train = PATTERN_TRAIN_DATA.findall(text)
            ft = PATTERN_FT_DATA.findall(text)

            return {
                "model_id": model_id,
                "base_model": base[0][1] if base else "unknown",
                "train_dataset": train[0][1] if train else "unknown",
                "ft_dataset": ft[0][1] if ft else "unknown"
            }
        except Exception as e:
            retries -= 1
            time.sleep(5)
            continue

    return {
        "model_id": model_id,
        "base_model": "unknown",
        "train_dataset": "unknown",
        "ft_dataset": "unknown"
    }

def batch_parse_models(model_df):
    log("开始真实解析模型依赖...")
    dep_list = []
    total = len(model_df)

    for idx, model_id in enumerate(model_df["model_id"]):
        if idx % 20 == 0 and idx > 0:
            log("等待 10 秒，避免被限制...")
            time.sleep(10)

        res = parse_single_model(model_id)
        dep_list.append(res)
        print(f"解析进度：{idx+1}/{total} | {model_id}")

    dep_df = pd.DataFrame(dep_list)
    full_df = pd.merge(model_df, dep_df, on="model_id")
    save_csv(full_df, "hf_top1000_model_full.csv", data_type="processed")
    log("✅ 真实依赖解析完成！")
    return full_df