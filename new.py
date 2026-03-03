from huggingface_hub import HfApi

api = HfApi()

# 1. 获取模型元数据 (前 1000 个)
models = api.list_models(limit=1000, sort="downloads")
model_data = []
for m in models:
    model_data.append({
        "id": m.modelId,
        "author": m.author,
        "last_modified": m.lastModified,
        "downloads": m.downloads,
        "tags": m.tags
    })

# 2. 获取数据集元数据 (前 1000 个)
datasets = api.list_datasets(limit=1000, sort="downloads")
dataset_data = []
for d in datasets:
    dataset_data.append({
        "id": d.id,
        "author": d.author,
        "description": getattr(d, 'description', 'N/A'),
        "downloads": d.downloads
    })

for d in model_data:
    print(d)
for d in dataset_data:
    print(d)

print(f"成功获取 {len(model_data)} 个模型和 {len(dataset_data)} 个数据集的信息。")

#313213212


