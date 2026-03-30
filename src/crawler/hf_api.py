# src/crawler/hf_api.py
from huggingface_hub import list_models, ModelFilter, login
from src.config.settings import HF_TOKEN, TOP_MODELS_LIMIT, BATCH_SIZE
from src.utils.common import log, save_csv

# 登录Hugging Face
login(token=HF_TOKEN, add_to_git_credential=False)

def get_top_models(limit=TOP_MODELS_LIMIT):
    log(f"开始获取 Top {limit} 热门模型")
    model_filter = ModelFilter(has_model_card=True)
    all_models = []

    # 分页爬取
    for i in range(10):
        batch = list_models(
            filter=model_filter,
            sort="downloads",
            direction=-1,
            limit=BATCH_SIZE,
            offset=i * BATCH_SIZE
        )
        all_models.extend(batch)
        if len(all_models) >= limit:
            break

    all_models = all_models[:limit]
    log(f"共获取 {len(all_models)} 个模型")

    # 构建数据表
    df = pd.DataFrame({
        "model_id": [m.modelId for m in all_models],
        "author": [m.author for m in all_models],
        "downloads": [m.downloads for m in all_models],
        "license": [m.license or "unknown" for m in all_models],
        "task": [m.task[0] if m.task else "unknown" for m in all_models],
        "last_modified": [m.lastModified for m in all_models]
    })

    save_csv(df, "hf_top1000_model_base.csv", data_type="raw")
    return df

# 测试：单独运行此文件，看能否成功爬取数据
if __name__ == "__main__":
    get_top_models()