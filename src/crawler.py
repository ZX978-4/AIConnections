from huggingface_hub import list_models, model_info
from .database_manager import DatabaseManager
import time


def run_crawler(limit=100):
    db = DatabaseManager()
    print("开始爬取供应链数据...")

    models = list_models(sort="downloads", limit=limit)

    for m in models:
        try:
            info = model_info(m.modelId)
            # 1. 存入详情
            db.save_model_info(info.modelId, info.author, getattr(info, 'downloads', 0))

            # 2. 提取并存入关系
            card = getattr(info, 'cardData', {})
            if card:
                # 处理 base_model
                base = card.get('base_model')
                if base:
                    db.add_relation(info.modelId, str(base), "DERIVED_FROM")

                # 处理 datasets
                datasets = card.get('datasets', [])
                if isinstance(datasets, str): datasets = [datasets]
                for ds in datasets:
                    db.add_relation(info.modelId, ds, "TRAINED_ON")

            print(f"成功处理: {info.modelId}")
            time.sleep(0.5)
        except Exception as e:
            print(f"跳过 {m.modelId}: {e}")

    db.close()