from huggingface_hub import HfApi
import time
from src.config.settings import HF_TOKEN, TOP_K_MODELS
from src.utils.common import logger, clean_license
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
            # 应用证书清洗
            raw_license = getattr(ds_info.cardData, 'license', 'unknown') if ds_info.cardData else 'unknown'

            self.dataset_data_store[dataset_id] = {
                "id": dataset_id,
                "type": "dataset",
                "downloads": getattr(ds_info, 'downloads', 0),
                "author": getattr(ds_info, 'author', 'unknown'),
                "license": clean_license(raw_license)  # 使用清洗函数
            }
        except:
            self.dataset_data_store[dataset_id] = {"id": dataset_id, "type": "dataset", "error": "inaccessible"}

    def _calculate_dynamic_limit(self, downloads):
        """
        根据模型的下载量定义爬取子节点的数量。
        策略：越火的模型，越值得深挖其衍生的生态系统。
        """
        if downloads > 1000000:
            return 50  # 超级基座（Llama/Mistral系列），值得深度挖掘完整生态
        elif downloads > 100000:
            return 30  # 顶流模型
        elif downloads > 10000:
            return 15  # 热门模型
        elif downloads > 1000:
            return 10  # 普通模型（从5提高到10，增加样本多样性）
        elif downloads > 100:
            return 5  # 有一定关注度的长尾模型
        else:
            return 2  # 几乎无人使用的模型

    def fetch_model_and_dependencies(self, model_id, depth=0):
        if model_id in self.visited_models or depth > 8:
            return

        self.visited_models.add(model_id)
        indent = "  " * depth
        logger.info(f"{indent}--> Processing {model_id} (Depth: {depth})")

        try:
            info = self.api.model_info(model_id)
            # 获取下载量用于动态策略
            downloads = getattr(info, 'downloads', 0)

            # --- 动态策略核心：计算当前模型的 limit ---
            dynamic_limit = self._calculate_dynamic_limit(downloads)
            logger.info(f"{indent}    Downloads: {downloads}, Limit set to: {dynamic_limit}")

            # 记录数据集和基础信息（保持原逻辑）
            ds_ids = [t.replace("dataset:", "") for t in (info.tags or []) if t.startswith("dataset:")]
            for ds_id in ds_ids:
                self.fetch_dataset_info(ds_id)
            raw_license = getattr(info.cardData, 'license', 'unknown') if info.cardData else 'unknown'
            self.model_data_store[model_id] = {
                "id": model_id,
                "type": "model",
                "task": getattr(info, 'pipeline_tag', 'unknown'),
                "downloads": downloads,
                "author": getattr(info, 'author', 'unknown'),
                "license": clean_license(raw_license),
                "datasets": ds_ids,
                "edges": self.model_data_store.get(model_id, {}).get("edges", [])
            }

            # --- 关键修改：将 dynamic_limit 传递给 web_parser ---
            rel_data = self.web_parser.get_model_relationships(model_id, limit=dynamic_limit)

            if rel_data["downstream"]:
                logger.info(f"{indent}    Found {len(rel_data['downstream'])} downstream models.")

            for child in rel_data["downstream"]:
                self._add_edge(model_id, child['id'], child['type'])
                self.fetch_model_and_dependencies(child['id'], depth + 1)
                time.sleep(0.1)  # 礼貌延时

            # 处理上游逻辑（保持原逻辑）
            if info.cardData and 'base_model' in info.cardData:
                bm = info.cardData['base_model']
                # 兼容字符串或列表格式
                bases = [bm] if isinstance(bm, str) else bm

                for b_id in bases:
                    # 确保 b_id 是合法的字符串（有时元数据可能不规范）
                    if isinstance(b_id, str) and b_id.strip():
                        # 1. 添加边：父模型 (b_id) -> 当前模型 (model_id)
                        self._add_edge(b_id, model_id, "base_of")

                        # 2. 递归检查：如果父模型没被访问过，且未超过最大深度，则主动抓取
                        if b_id not in self.visited_models and depth <= 8:
                            logger.info(f"{indent}    发现上游父模型: {b_id}，开始追溯...")
                            self.fetch_model_and_dependencies(b_id, depth + 1)

        except Exception as e:
            logger.error(f"{indent}    Error processing {model_id}: {e}")