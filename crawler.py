
import json
from src.crawler.hf_api import HFGraphCrawler
from src.builder.graph_builder import SupplyChainBuilder
from src.config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.utils.common import logger, save_json

LIMIT=100

def main():
    crawler = HFGraphCrawler()
    seeds = crawler.get_top_models(limit=LIMIT)

    # --- 续爬检查 ---
    checkpoint_path = RAW_DATA_DIR / "supply_chain_checkpoint.json"
    if checkpoint_path.exists():
        try:
            with open(checkpoint_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                crawler.model_data_store = data.get("models", {})
                crawler.dataset_data_store = data.get("datasets", {})
                crawler.visited_models = set(crawler.model_data_store.keys())
            logger.info(f"Resuming from checkpoint: {len(crawler.visited_models)} models loaded.")
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")

    # 过滤掉已爬取的种子
    remaining_seeds = [s for s in seeds if s not in crawler.visited_models]
    save_interval = 10

    try:
        for idx, mid in enumerate(remaining_seeds):
            logger.info(f"Progress: {idx + 1}/{len(remaining_seeds)} - {mid}")
            crawler.fetch_model_and_dependencies(mid)

            if (idx + 1) % save_interval == 0:
                save_json({"models": crawler.model_data_store, "datasets": crawler.dataset_data_store}, checkpoint_path)
                logger.info("Checkpoint saved.")
    except KeyboardInterrupt:
        logger.info("Manual stop. Saving data...")
    finally:
        # 最终保存
        full_data = {"models": crawler.model_data_store, "datasets": crawler.dataset_data_store}
        save_json(full_data, RAW_DATA_DIR / "full_supply_chain_data.json")

        builder = SupplyChainBuilder(crawler.model_data_store, crawler.dataset_data_store)
        nodes_df, edges_df = builder.process()
        nodes_df.to_csv(PROCESSED_DATA_DIR / "nodes.csv", index=False, encoding='utf-8-sig')
        edges_df.to_csv(PROCESSED_DATA_DIR / "edges.csv", index=False, encoding='utf-8-sig')
        logger.info(f"Exported {len(nodes_df)} nodes and {len(edges_df)} edges.")


if __name__ == "__main__":
    main()