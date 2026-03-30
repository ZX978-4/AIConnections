import time
from src.crawler.hf_api import HFGraphCrawler
from src.builder.graph_builder import SupplyChainBuilder
from src.config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.utils.common import logger, save_json


def main():
    crawler = HFGraphCrawler()
    # 建议先用 limit=50 测试，确认 edges.csv 里的关系和 license 没问题
    seeds = crawler.get_top_models(limit=100)

    try:
        for mid in seeds:
            crawler.fetch_model_and_dependencies(mid)
    except KeyboardInterrupt:
        logger.info("Interrupted. Saving progress...")

    # 保存原始 JSON
    save_json(crawler.model_data_store, RAW_DATA_DIR / "raw_supply_chain.json")

    # 构建并保存 CSV
    builder = SupplyChainBuilder(crawler.model_data_store)
    nodes, edges = builder.process()

    nodes.to_csv(PROCESSED_DATA_DIR / "nodes.csv", index=False)
    edges.to_csv(PROCESSED_DATA_DIR / "edges.csv", index=False)

    logger.info(f"Done! Extracted {len(nodes)} models and {len(edges)} relationships.")


if __name__ == "__main__":
    main()