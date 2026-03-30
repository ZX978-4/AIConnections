# src/builder/graph_builder.py
import networkx as nx
import pandas as pd
import os
from src.config.settings import SAVE_PATHS
from src.utils.common import log

def build_supply_chain_graph(full_df):
    log("开始构建AI模型供应链图谱...")
    valid_df = full_df[full_df["base_model"] != "unknown"]
    valid_df = valid_df[valid_df["base_model"] != "access_denied"]

    # === 1. 构建节点 ===
    model_nodes = valid_df[["model_id", "author", "downloads", "license", "task"]].rename(columns={"model_id": "node_id"})
    model_nodes["node_type"] = "model"

    datasets = list(valid_df["train_dataset"].unique()) + list(valid_df["ft_dataset"].unique())
    dataset_nodes = pd.DataFrame({
        "node_id": [d for d in datasets if d not in ["unknown", "access_denied"]]
    })
    dataset_nodes["node_type"] = "dataset"

    # === 2. 构建边 ===
    m2m = valid_df[["model_id", "base_model", "downloads"]].rename(columns={"model_id": "source", "base_model": "target", "downloads": "weight"})
    m2m["type"] = "finetune_on"

    m2d = valid_df[["model_id", "ft_dataset", "downloads"]].rename(columns={"model_id": "source", "ft_dataset": "target", "downloads": "weight"})
    m2d = m2d[m2d["target"] != "unknown"]
    m2d["type"] = "use_dataset"

    edges = pd.concat([m2m, m2d], ignore_index=True)

    # === 3. 生成图 ===
    G = nx.DiGraph(name="AI_Supply_Chain")
    for _, n in model_nodes.iterrows():
        G.add_node(n["node_id"], type="model", color="#1f77b4")
    for _, n in dataset_nodes.iterrows():
        G.add_node(n["node_id"], type="dataset", color="#d62728")
    for _, e in edges.iterrows():
        G.add_edge(e["source"], e["target"], type=e["type"], weight=e["weight"])

    # 保存图谱
    gexf_path = os.path.join(SAVE_PATHS["graphs"], "supply_chain.gexf")
    nx.write_gexf(G, gexf_path)
    log(f"图谱已保存：{gexf_path}")
    return G