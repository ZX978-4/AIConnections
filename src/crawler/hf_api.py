from huggingface_hub import HfApi
import time
from src.config.settings import HF_TOKEN, TOP_K_MODELS, PROCESSED_DATA_DIR
from src.utils.common import logger, clean_license, save_json
from src.parser.model_parser import HFWebParser


class HFGraphCrawler:
    def __init__(self):
        self.api = HfApi(token=HF_TOKEN)
        self.web_parser = HFWebParser()
        self.visited_models = set()
        self.visited_datasets = set()
        self.model_data_store = {}
        self.dataset_data_store = {}
        self.counter = 0  # 用于触发定期保存

    def save_checkpoint(self):
        """断点续传：保存当前爬取的内存快照"""
        checkpoint = {
            "visited_models": list(self.visited_models),
            "model_data_store": self.model_data_store,
            "dataset_data_store": self.dataset_data_store
        }
        save_json(checkpoint, PROCESSED_DATA_DIR / "crawler_checkpoint.json")
        logger.info("Checkpoint saved to disk.")

    def get_top_models(self, limit=TOP_K_MODELS):
        logger.info(f"Fetching top {limit} seed models...")
        try:
            models = self.api.list_models(sort="downloads", direction=-1, limit=limit)
            return [m.id for m in models]
        except Exception as e:
            logger.error(f"Failed to fetch seeds: {e}")
            return []

    def _add_edge(self, source, target, relation):
        """确保边关系的唯一性与类型准确性"""
        if source not in self.model_data_store:
            self.model_data_store[source] = {"id": source, "edges": []}

        edges = self.model_data_store[source].setdefault("edges", [])
        # 如果边已存在且当前是 base_of，则保留更具体的下游类型
        existing = next((e for e in edges if e["to"] == target), None)
        if not existing:
            edges.append({"to": target, "relation": relation})
        elif relation != "base_of":
            existing["relation"] = relation

    def fetch_dataset_info(self, dataset_id):
        if dataset_id in self.visited_datasets: return
        self.visited_datasets.add(dataset_id)
        try:
            ds_info = self.api.dataset_info(dataset_id)
            raw_license = getattr(ds_info.cardData, 'license', 'unknown') if ds_info.cardData else 'unknown'

            self.dataset_data_store[dataset_id] = {
                "id": dataset_id,
                "type": "dataset",
                "downloads": getattr(ds_info, 'downloads', 0),
                "author": getattr(ds_info, 'author', 'unknown'),
                "license": clean_license(raw_license)
            }
        except:
            self.dataset_data_store[dataset_id] = {"id": dataset_id, "type": "dataset", "error": "inaccessible"}

    def _calculate_dynamic_limit(self, downloads):
        """根据热度动态分配爬取深度，优化资源分配"""
        if downloads > 1000000:
            return 50
        elif downloads > 100000:
            return 30
        elif downloads > 10000:
            return 15
        elif downloads > 1000:
            return 10
        else:
            return 3

    def fetch_model_and_dependencies(self, model_id, depth=0):
        if model_id in self.visited_models or depth > 5:  # 稍微缩减深度限制防止死循环
            return

        self.visited_models.add(model_id)
        self.counter += 1

        # 每爬取 50 个节点自动保存一次
        if self.counter % 50 == 0:
            self.save_checkpoint()

        indent = "  " * depth
        logger.info(f"{indent}--> Processing {model_id} (Depth: {depth})")

        try:
            # 使用官方 API 获取基础元数据
            info = self.api.model_info(model_id)
            downloads = getattr(info, 'downloads', 0)
            dynamic_limit = self._calculate_dynamic_limit(downloads)

            # 提取数据集依赖
            ds_ids = [t.replace("dataset:", "") for t in (info.tags or []) if t.startswith("dataset:")]
            for ds_id in ds_ids:
                self.fetch_dataset_info(ds_id)

            raw_license = getattr(info.cardData, 'license', 'unknown') if info.cardData else 'unknown'

            # 更新模型存储信息
            self.model_data_store[model_id] = {
                **self.model_data_store.get(model_id, {}),
                "id": model_id,
                "type": "model",
                "task": getattr(info, 'pipeline_tag', 'unknown'),
                "downloads": downloads,
                "author": getattr(info, 'author', 'unknown'),
                "license": clean_license(raw_license),
                "datasets": ds_ids
            }

            # 抓取下游衍生模型 (微调, 合并, 蒸馏等)
            rel_data = self.web_parser.get_model_relationships(model_id, limit=dynamic_limit)

            for child in rel_data["downstream"]:
                self._add_edge(model_id, child['id'], child['type'])
                self.fetch_model_and_dependencies(child['id'], depth + 1)
                time.sleep(0.2)  # 增加延时以应对反爬

            # 处理上游 Base Model 溯源
            if info.cardData and 'base_model' in info.cardData:
                bm = info.cardData['base_model']
                bases = [bm] if isinstance(bm, str) else (bm if isinstance(bm, list) else [])

                for b_id in bases:
                    if isinstance(b_id, str) and b_id.strip():
                        self._add_edge(b_id, model_id, "base_of")
                        if b_id not in self.visited_models:
                            self.fetch_model_and_dependencies(b_id, depth + 1)

        except Exception as e:
            logger.error(f"{indent}    Error processing {model_id}: {e}")