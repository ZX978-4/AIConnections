import pandas as pd
from pyvis.network import Network
import os

def generate_pyvis_graph(output_path="output/html/supply_chain_graph.html"):
    """生成交互式网络图谱"""
    nodes_df = pd.read_csv("data/processed/nodes.csv")
    edges_df = pd.read_csv("data/processed/edges.csv")

    # 创建网络对象
    net = Network(height="750px", width="100%", directed=True, notebook=False)
    net.physics.enabled = True
    net.physics.barnesHut.gravitationalConstance = -80000
    net.physics.barnesHut.centralGravity = 0.3
    net.physics.barnesHut.springLength = 250

    # 定义节点颜色和大小
    color_map = {"model": "#FF6B6B", "dataset": "#4ECDC4"}
    
    # 添加节点
    for _, row in nodes_df.iterrows():
        title = f"ID: {row['id']}<br>Type: {row['type']}<br>Author: {row['author']}<br>Downloads: {row['downloads']}"
        color = color_map.get(row['type'], "#95E1D3")
        
        # 根据下载量调整节点大小
        size = min(50, max(10, 10 + row['downloads'] / 10000000))
        
        net.add_node(row["id"], 
                     label=row["id"].split("/")[-1],  # 只显示模型名
                     title=title,
                     color=color,
                     size=size)

    # 定义边的颜色和样式
    relation_colors = {
        "fine-tune": "#FF6B9D",
        "quantization": "#FFA500",
        "trained_on": "#4ECDC4",
        "merge": "#95E1D3",
        "distillation": "#C7CEEA"
    }

    # 添加边
    for _, row in edges_df.iterrows():
        color = relation_colors.get(row['relation'], "#CCCCCC")
        net.add_edge(row["source"], row["target"], 
                    title=row['relation'],
                    color=color,
                    label=row['relation'])

    # 配置物理引擎和交互
    net.show_buttons(filter_=['physics'])
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    net.show(output_path)
    print(f"✅ 交互式图谱已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    generate_pyvis_graph()
