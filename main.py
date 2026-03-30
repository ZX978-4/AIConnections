# main.py
from src.crawler.hf_api import get_top_models
from src.parser.model_parser import batch_parse_models
from src.builder.graph_builder import build_supply_chain_graph
from src.analyzer.stats_analyzer import run_quantitative_analysis
from src.visualizer.pyvis_builder import generate_interactive_graph

if __name__ == "__main__":
    print("=" * 50)
    print("  AI模型供应链全流程启动 ")
    print("=" * 50)

    # 1. 爬取模型
    model_df = get_top_models()

    # 2. 解析依赖
    full_df = batch_parse_models(model_df)

    # 3. 构建图谱
    G = build_supply_chain_graph(full_df)

    # 4. 数据分析
    run_quantitative_analysis(full_df)

    # 5. 可视化
    generate_interactive_graph(G)

    print("=" * 50)
    print("  全部完成！🎉")
    print("  数据在 data/ 文件夹")
    print("  输出在 output/ 文件夹")
    print("=" * 50)