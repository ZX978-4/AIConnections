import os
import pandas as pd
import streamlit as st

@st.cache_data
def load_data(data_dir: str = "data/processed"):
    """加载节点和边数据，无数据时自动生成示例数据"""
    os.makedirs(data_dir, exist_ok=True)

    nodes_path = os.path.join(data_dir, "nodes.csv")
    edges_path = os.path.join(data_dir, "edges.csv")

    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        st.warning("未检测到数据文件，已自动生成Hugging Face模型示例数据")
        nodes_data = [
            {"id": "meta-llama/Llama-3-70B", "type": "model", "author": "meta-llama", "downloads": 5000000, "license": "LLAMA 3", "params": "70B"},
            {"id": "meta-llama/Llama-3-8B", "type": "model", "author": "meta-llama", "downloads": 12000000, "license": "LLAMA 3", "params": "8B"},
            {"id": "HuggingFaceH4/zephyr-7b-beta", "type": "model", "author": "HuggingFaceH4", "downloads": 1500000, "license": "MIT", "params": "7B"},
            {"id": "lmsys/vicuna-7b-v1.5", "type": "model", "author": "lmsys", "downloads": 2300000, "license": "Apache 2.0", "params": "7B"},
            {"id": "EleutherAI/the-pile", "type": "dataset", "author": "EleutherAI", "downloads": 800000, "license": "MIT", "params": "-"},
            {"id": "mistralai/Mistral-7B-v0.1", "type": "model", "author": "mistralai", "downloads": 8000000, "license": "Apache 2.0", "params": "7B"},
            {"id": "mistralai/Mistral-7B-Instruct", "type": "model", "author": "mistralai", "downloads": 6000000, "license": "Apache 2.0", "params": "7B"},
            {"id": "HuggingFaceH4/zephyr-7b-alpha", "type": "model", "author": "HuggingFaceH4", "downloads": 800000, "license": "MIT", "params": "7B"},
            {"id": "openlm-research/open_llama_7b", "type": "model", "author": "openlm-research", "downloads": 3000000, "license": "Apache 2.0", "params": "7B"},
            {"id": "chavinlo/alpaca-native", "type": "model", "author": "chavinlo", "downloads": 500000, "license": "CC BY-NC 4.0", "params": "7B"},
        ]
        edges_data = [
            {"source": "meta-llama/Llama-3-8B", "target": "HuggingFaceH4/zephyr-7b-beta", "relation": "BASED_ON"},
            {"source": "meta-llama/Llama-3-8B", "target": "lmsys/vicuna-7b-v1.5", "relation": "BASED_ON"},
            {"source": "EleutherAI/the-pile", "target": "meta-llama/Llama-3-8B", "relation": "TRAINED_ON"},
            {"source": "EleutherAI/the-pile", "target": "meta-llama/Llama-3-70B", "relation": "TRAINED_ON"},
            {"source": "mistralai/Mistral-7B-v0.1", "target": "mistralai/Mistral-7B-Instruct", "relation": "FINE_TUNED"},
            {"source": "meta-llama/Llama-3-8B", "target": "HuggingFaceH4/zephyr-7b-alpha", "relation": "BASED_ON"},
            {"source": "EleutherAI/the-pile", "target": "openlm-research/open_llama_7b", "relation": "TRAINED_ON"},
            {"source": "openlm-research/open_llama_7b", "target": "chavinlo/alpaca-native", "relation": "FINE_TUNED"},
            {"source": "chavinlo/alpaca-native", "target": "lmsys/vicuna-7b-v1.5", "relation": "MERGED_WITH"},
        ]
        nodes_df = pd.DataFrame(nodes_data)
        edges_df = pd.DataFrame(edges_data)
        nodes_df.to_csv(nodes_path, index=False)
        edges_df.to_csv(edges_path, index=False)
    else:
        nodes_df = pd.read_csv(nodes_path)
        edges_df = pd.read_csv(edges_path)

    required_node_cols = ["id", "type", "author", "downloads", "license"]
    required_edge_cols = ["source", "target", "relation"]
    if not all(col in nodes_df.columns for col in required_node_cols):
        st.error(f"节点数据缺少必填列，必须包含：{required_node_cols}")
        st.stop()
    if not all(col in edges_df.columns for col in required_edge_cols):
        st.error(f"边数据缺少必填列，必须包含：{required_edge_cols}")
        st.stop()

    return nodes_df, edges_df

@st.cache_data
def create_node_info_map(nodes_df):
    return nodes_df.set_index('id').to_dict('index')
