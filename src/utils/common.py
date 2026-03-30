# src/utils/common.py
import time
import os
import pandas as pd
from src.config.settings import SAVE_PATHS

# 防限流暂停
def rate_limit_sleep(seconds=5):
    print(f"[休眠] 暂停 {seconds} 秒，防止API限流")
    time.sleep(seconds)

# 统一保存CSV文件
def save_csv(df, filename, data_type="processed"):
    save_path = os.path.join(SAVE_PATHS[data_type], filename)
    df.to_csv(save_path, index=False, encoding="utf-8-sig")
    print(f"[保存] {save_path}")

# 日志输出
def log(msg):
    print(f"[INFO] {msg}")