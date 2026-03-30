# src/visualizer/pyvis_builder.py
from pyvis.network import Network
import networkx as nx
import os
from src.config.settings import SAVE_PATHS
from src.utils.common import log

def generate_interactive_graph(G):
    log("生成交互式可视化图谱...")
    net = Network(directed=True, height="800px", width="100%")
    net.from_nx(G)

    # 节点样式
    for node in net.nodes:
        node["size"] = 30
        node["title"] = f"ID: {node['id']}\n类型: {node.get('type', 'unknown')}"

    # 边样式
    for edge in net.edges:
        edge["width"] = 2
        edge["title"] = edge.get("type", "dependency")

    net.show_buttons(filter_=["physics"])
    html_path = os.path.join(SAVE_PATHS["html"], "supply_chain.html")
    net.write_html(html_path)
    log(f"交互式图谱已保存：{html_path}")