from huggingface_hub import HfApi
import time

from src.config.settings import HF_TOKEN, TOP_K_MODELS, PROCESSED_DATA_DIR
from src.parser.model_parser import HFWebParser
from src.utils.common import clean_license, logger, save_json


class HFGraphCrawler:
    def __init__(self):
        self.api = HfApi(token=HF_TOKEN)
        self.web_parser = HFWebParser()
        self.visited_models = set()
        self.visited_datasets = set()
        self.model_data_store = {}
        self.dataset_data_store = {}
        self.counter = 0

    def save_checkpoint(self):
        """Save crawler checkpoint to disk."""
        checkpoint = {
            "visited_models": list(self.visited_models),
            "model_data_store": self.model_data_store,
            "dataset_data_store": self.dataset_data_store,
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
        """Ensure edge uniqueness and keep the most specific relation."""
        if source not in self.model_data_store:
            self.model_data_store[source] = {"id": source, "edges": []}

        edges = self.model_data_store[source].setdefault("edges", [])
        existing = next((e for e in edges if e["to"] == target), None)
        if not existing:
            edges.append({"to": target, "relation": relation})
        elif relation != "base_of":
            existing["relation"] = relation

    def fetch_dataset_info(self, dataset_id):
        if dataset_id in self.visited_datasets:
            return
        self.visited_datasets.add(dataset_id)
        try:
            ds_info = self.api.dataset_info(dataset_id)
            raw_license = getattr(ds_info.cardData, "license", "unknown") if ds_info.cardData else "unknown"

            self.dataset_data_store[dataset_id] = {
                "id": dataset_id,
                "type": "dataset",
                "downloads": getattr(ds_info, "downloads", 0),
                "author": getattr(ds_info, "author", "unknown"),
                "license": clean_license(raw_license),
            }
        except Exception:
            self.dataset_data_store[dataset_id] = {"id": dataset_id, "type": "dataset", "error": "inaccessible"}

    def _calculate_dynamic_limit(self, downloads):
        """Allocate crawl depth based on popularity."""
        if downloads > 1_000_000:
            return 50
        if downloads > 100_000:
            return 30
        if downloads > 10_000:
            return 15
        if downloads > 1_000:
            return 10
        return 3

    def fetch_model_and_dependencies(self, model_id, depth=0):
        if model_id in self.visited_models or depth > 5:
            return

        self.visited_models.add(model_id)
        self.counter += 1

        if self.counter % 50 == 0:
            self.save_checkpoint()

        indent = "  " * depth
        logger.info(f"{indent}--> Processing {model_id} (Depth: {depth})")

        try:
            info = self.api.model_info(model_id)
            downloads = getattr(info, "downloads", 0)
            dynamic_limit = self._calculate_dynamic_limit(downloads)

            ds_ids = [t.replace("dataset:", "") for t in (info.tags or []) if t.startswith("dataset:")]
            for ds_id in ds_ids:
                self.fetch_dataset_info(ds_id)

            raw_license = getattr(info.cardData, "license", "unknown") if info.cardData else "unknown"

            self.model_data_store[model_id] = {
                **self.model_data_store.get(model_id, {}),
                "id": model_id,
                "type": "model",
                "task": getattr(info, "pipeline_tag", "unknown"),
                "downloads": downloads,
                "author": getattr(info, "author", "unknown"),
                "license": clean_license(raw_license),
                "datasets": ds_ids,
            }

            rel_data = self.web_parser.get_model_relationships(model_id, limit=dynamic_limit)

            for child in rel_data["downstream"]:
                self._add_edge(model_id, child["id"], child["type"])
                self.fetch_model_and_dependencies(child["id"], depth + 1)
                time.sleep(0.2)

            if info.cardData and "base_model" in info.cardData:
                bm = info.cardData["base_model"]
                bases = [bm] if isinstance(bm, str) else (bm if isinstance(bm, list) else [])

                for b_id in bases:
                    if isinstance(b_id, str) and b_id.strip():
                        self._add_edge(b_id, model_id, "base_of")
                        if b_id not in self.visited_models:
                            self.fetch_model_and_dependencies(b_id, depth + 1)

        except Exception as e:
            logger.error(f"{indent}    Error processing {model_id}: {e}")
