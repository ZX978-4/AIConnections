# src/crawler/hf_api.py 【最终无错版】
from huggingface_hub import list_models
from src.config.settings import TOP_MODELS_LIMIT, BATCH_SIZE
from src.utils.common import log, save_csv
import pandas as pd
import time

def get_top_models(limit=TOP_MODELS_LIMIT):
    log(f"开始爬取 Hugging Face 真实热门模型（无登录·防卡死版）...")
    all_models = []

    for i in range(20):
        try:
            log(f"正在抓取第 {i+1} 页数据...")

            batch = list_models(
                has_model_card=True,
                sort="downloads",
                direction=-1,
                limit=50,
                offset=i * 50,
                timeout=20
            )

            all_models.extend(batch)
            log(f"第 {i+1} 页抓取成功，当前总数：{len(all_models)}")
            time.sleep(6)

            if len(all_models) >= limit:
                break

        except Exception as e:
            log(f"等待 15 秒重试...")
            time.sleep(15)
            continue

    all_models = all_models[:limit]

    df = pd.DataFrame({
        "model_id": [m.modelId for m in all_models],
        "author": [m.author for m in all_models],
        "downloads": [m.downloads for m in all_models],
        "license": [m.license or "unknown" for m in all_models],
        "task": [m.task[0] if m.task else "unknown" for m in all_models],
        "last_modified": [m.lastModified for m in all_models]
    })

    save_csv(df, "hf_top1000_model_base.csv", data_type="raw")
    log(f"✅ 真实模型抓取完成！共 {len(df)} 个！")
    return df