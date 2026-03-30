# src/parser/model_parser.py
from huggingface_hub import get_model_readme
from bs4 import BeautifulSoup
from src.config.settings import PATTERN_BASE_MODEL, PATTERN_TRAIN_DATA, PATTERN_FT_DATA, SLEEP_INTERVAL
from src.utils.common import log, rate_limit_sleep, save_csv
import pandas as pd

def parse_single_model(model_id):
    try:
        readme = get_model_readme(model_id)
        soup = BeautifulSoup(readme, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        base = PATTERN_BASE_MODEL.findall(text)
        train = PATTERN_TRAIN_DATA.findall(text)
        ft = PATTERN_FT_DATA.findall(text)

        return {
            "model_id": model_id,
            "base_model": base[0][1] if base else "unknown",
            "train_dataset": train[0][1] if train else "unknown",
            "ft_dataset": ft[0][1] if ft else (train[0][1] if train else "unknown")
        }
    except Exception as e:
        return {
            "model_id": model_id,
            "base_model": "access_denied",
            "train_dataset": "access_denied",
            "ft_dataset": "access_denied"
        }

def batch_parse_models(model_df):
    log("开始批量解析模型依赖...")
    dep_list = []

    for idx, model_id in enumerate(model_df["model_id"]):
        if idx % 50 == 0 and idx > 0:
            rate_limit_sleep(SLEEP_INTERVAL)

        res = parse_single_model(model_id)
        dep_list.append(res)
        print(f"解析进度: {idx+1}/{len(model_df)} -> {model_id}")

    dep_df = pd.DataFrame(dep_list)
    full_df = pd.merge(model_df, dep_df, on="model_id")
    save_csv(full_df, "hf_top1000_model_full.csv", data_type="processed")
    return full_df