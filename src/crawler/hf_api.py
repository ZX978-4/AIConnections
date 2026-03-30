from huggingface_hub import HfApi
import time
import os
from src.config.settings import HF_TOKEN, TOP_K_MODELS
from src.utils.common import logger
from src.parser.model_parser import HFWebParser


class HFGraphCrawler:
    def __init__(self):
        # 如果依然报 10054 错误，取消下面一行的注释使用镜像
        # os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        self.api = HfApi(token=HF_TOKEN)
        self.web_parser = HFWebParser()
        self.visited_models = set()
        self.model_data_store = {}

    def get_top_models(self, limit=TOP_K_MODELS):
        logger.info(f"Fetching top {limit} models...")
        try:
            models = self.api.list_models(sort="downloads", direction=-1, limit=limit)
            return [m.id for m in models]
        except Exception as e:
            logger.error(f"Failed to fetch seed models: {e}")
            return []

    def _add_edge(self, source, target, relation):
        """记录边并去重，具体关系(finetune)优于模糊关系(base_of)"""
        if source not in self.model_data_store:
            self.model_data_store[source] = {"id": source, "edges": []}

        edges = self.model_data_store[source]["edges"]
        for edge in edges:
            if edge["to"] == target:
                if relation != "base_of":  # 如果新关系更具体，更新它
                    edge["relation"] = relation
                return
        edges.append({"to": target, "relation": relation})

    def fetch_model_and_dependencies(self, model_id, depth=0):
        if model_id in self.visited_models or depth > 2:
            return

        self.visited_models.add(model_id)
        logger.info(f"{'  ' * depth}Exploring: {model_id}")

        try:
            info = self.api.model_info(model_id)

            # 提取 License
            m_license = "unknown"
            if info.cardData and 'license' in info.cardData:
                m_license = info.cardData['license']
            else:
                for tag in (info.tags or []):
                    if tag.startswith("license:"):
                        m_license = tag.replace("license:", "")
                        break

            # 初始化节点数据
            if model_id not in self.model_data_store or "author" not in self.model_data_store[model_id]:
                self.model_data_store[model_id] = {
                    "id": model_id,
                    "downloads": getattr(info, 'downloads', 0),
                    "author": getattr(info, 'author', 'unknown'),
                    "license": str(m_license),
                    "edges": self.model_data_store.get(model_id, {}).get("edges", []),
                    "datasets": [t.replace("dataset:", "") for t in info.tags if
                                 t.startswith("dataset:")] if info.tags else []
                }

            # 1. 处理下游 (Model Tree)
            rel_data = self.web_parser.get_model_relationships(model_id)
            for child in rel_data["downstream"]:
                self._add_edge(model_id, child['id'], child['type'])
                time.sleep(0.1)
                self.fetch_model_and_dependencies(child['id'], depth + 1)

            # 2. 处理上游 (Base Models - 支持多个)
            if info.cardData and 'base_model' in info.cardData:
                bm = info.cardData['base_model']
                bases = [bm] if isinstance(bm, str) else bm
                for b_id in bases:
                    if b_id and isinstance(b_id, str):
                        self._add_edge(b_id, model_id, "base_of")

        except Exception as e:
            logger.error(f"Failed at {model_id}: {e}")