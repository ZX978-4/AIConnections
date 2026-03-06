from huggingface_hub import HfApi
import pandas as pd
import json
import time

LIMIT =100
api = HfApi()

# 1. 获取模型元数据 
models = api.list_models(limit=LIMIT, sort="downloads")
model_data = []
for m in models:

    model_info_dict={
        "id": m.modelId,
        # "author": m.author if m.author else "未知作者",
        # "last_modified": m.lastModified if m.lastModified else "未知时间",
        "downloads": m.downloads if m.downloads else 0,
        "library_name" : m.library_name if m.library_name else "未知框架",
        "base_model": "无",
        # "dataset_deps": [],
        # "tags": ",".join(m.tags) if m.tags else "无标签"
    }

    #获取base_model和dataset_deps
    try:
        # time.sleep(0.01)
        model_info = api.model_info(m.modelId)
        card_data = model_info.cardData or {}

        base_model = card_data.get("base_model", "无")
        model_info_dict["base_model"]=base_model

        dataset_deps = card_data.get("datasets", [])
        model_info_dict["dataset_deps"]=dataset_deps
    except Exception as e:
        print(f"提取 {m.modelId} 依赖失败：{str(e)[:50]}")
        model_info_dict["base_model"]="获取失败"
        model_info_dict["dataset_deps"]="获取失败"

    model_data.append(model_info_dict)
    

# 2. 获取数据集元数据 
datasets = api.list_datasets(limit=LIMIT, sort="downloads")
dataset_data = []
for d in datasets:
    dataset_data.append({
        "dataset_id": d.id,
        "author": d.author if d.author else "未知",
        # "description": getattr(d, 'description', 'N/A'),
        "downloads": d.downloads if d.downloads else 0,
    })

pd.DataFrame(model_data).to_csv("data/models.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(model_data).to_json("data/models.json", orient="records", force_ascii=False, indent=4)
pd.DataFrame(dataset_data).to_csv("data/datasets.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(dataset_data).to_json("data/datasets.json", orient="records", force_ascii=False, indent=4)


print(f"成功获取 {len(model_data)} 个模型和 {len(dataset_data)} 个数据集的信息。")



