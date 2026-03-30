from huggingface_hub import HfApi
import time
from src.config.settings import HF_TOKEN, TOP_K_MODELS
from src.utils.common import logger
from src.parser.model_parser import HFWebParser


class HFGraphCrawler:
    def __init__(self):
        self.api = HfApi(token=HF_TOKEN)
        self.web_parser = HFWebParser()
        self.visited_models = set()
        self.visited_datasets = set()
        self.model_data_store = {}
        self.dataset_data_store = {}

    def get_top_models(self, limit=TOP_K_MODELS):
        logger.info(f"Fetching top {limit} seed models...")
        try:
            models = self.api.list_models(sort="downloads", direction=-1, limit=limit)
            return [m.id for m in models]
        except Exception as e:
            logger.error(f"Failed to fetch seeds: {e}")
            return []

    def _add_edge(self, source, target, relation):
        if source not in self.model_data_store:
            self.model_data_store[source] = {"id": source, "edges": []}
        edges = self.model_data_store[source].setdefault("edges", [])
        if not any(e["to"] == target for e in edges):
            edges.append({"to": target, "relation": relation})
        elif relation != "base_of":  # 更新为更具体的关系
            for e in edges:
                if e["to"] == target: e["relation"] = relation

    def fetch_dataset_info(self, dataset_id):
        if dataset_id in self.visited_datasets: return
        self.visited_datasets.add(dataset_id)
        try:
            ds_info = self.api.dataset_info(dataset_id)
            self.dataset_data_store[dataset_id] = {
                "id": dataset_id,
                "type": "dataset",
                "downloads": getattr(ds_info, 'downloads', 0),
                "author": getattr(ds_info, 'author', 'unknown'),
                "license": getattr(ds_info.cardData, 'license', 'unknown') if ds_info.cardData else 'unknown'
            }
        except:
            self.dataset_data_store[dataset_id] = {"id": dataset_id, "type": "dataset", "error": "inaccessible"}

    def fetch_model_and_dependencies(self, model_id, depth=0):
        # 即使被访问过，也打印一下跳过信息，让你知道程序在动
        if model_id in self.visited_models:
            return
        if depth > 2:
            return

        self.visited_models.add(model_id)
        # --- 关键：每一层递归都打印，让你看到进度 ---
        indent = "  " * depth
        logger.info(f"{indent}--> Processing {model_id} (Depth: {depth})")

        try:
            info = self.api.model_info(model_id)

            # 记录数据集
            ds_ids = [t.replace("dataset:", "") for t in (info.tags or []) if t.startswith("dataset:")]
            if ds_ids:
                logger.info(f"{indent}    Found {len(ds_ids)} datasets: {', '.join(ds_ids[:3])}...")

            for ds_id in ds_ids:
                self.fetch_dataset_info(ds_id)

            # 存储模型基础信息
            self.model_data_store[model_id] = {
                "id": model_id,
                "type": "model",
                "downloads": getattr(info, 'downloads', 0),
                "author": getattr(info, 'author', 'unknown'),
                "license": getattr(info.cardData, 'license', 'unknown') if info.cardData else 'unknown',
                "datasets": ds_ids,
                "edges": self.model_data_store.get(model_id, {}).get("edges", [])
            }

            # 处理下游
            rel_data = self.web_parser.get_model_relationships(model_id)
            if rel_data["downstream"]:
                logger.info(f"{indent}    Found {len(rel_data['downstream'])} downstream models.")

            for child in rel_data["downstream"]:
                # 这里会触发递归，进入下一层打印
                self._add_edge(model_id, child['id'], child['type'])
                self.fetch_model_and_dependencies(child['id'], depth + 1)
                time.sleep(0.1)  # 礼貌延时

            # 处理上游
            if info.cardData and 'base_model' in info.cardData:
                bm = info.cardData['base_model']
                bases = [bm] if isinstance(bm, str) else bm
                for b_id in bases:
                    if isinstance(b_id, str):
                        self._add_edge(b_id, model_id, "base_of")

        except Exception as e:
            logger.error(f"{indent}    Error processing {model_id}: {e}")