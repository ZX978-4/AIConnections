import os
import pandas as pd
import streamlit as st

from src.utils.sample_data import get_sample_nodes_edges


@st.cache_data
def load_data(data_dir: str = "data/processed"):
    """Load nodes/edges data; create sample data if missing."""
    os.makedirs(data_dir, exist_ok=True)

    nodes_path = os.path.join(data_dir, "nodes.csv")
    edges_path = os.path.join(data_dir, "edges.csv")

    if not os.path.exists(nodes_path) or not os.path.exists(edges_path):
        st.warning("No data found. Generated sample Hugging Face lineage data.")
        nodes_data, edges_data = get_sample_nodes_edges()
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
        st.error(f"Missing required node columns: {required_node_cols}")
        st.stop()
    if not all(col in edges_df.columns for col in required_edge_cols):
        st.error(f"Missing required edge columns: {required_edge_cols}")
        st.stop()

    return nodes_df, edges_df


@st.cache_data
def create_node_info_map(nodes_df):
    return nodes_df.set_index("id").to_dict("index")
