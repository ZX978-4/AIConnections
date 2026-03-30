import pandas as pd


class SupplyChainBuilder:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    def process(self):
        nodes = []
        edges = []

        for mid, info in self.raw_data.items():
            # 提取节点信息
            nodes.append({
                "id": mid,
                "downloads": info.get('downloads', 0),
                "author": info.get('author', 'unknown'),
                "license": info.get('license', 'unknown')
            })

            # 提取关系信息
            for edge in info.get('edges', []):
                edges.append({
                    "source": mid,
                    "target": edge["to"],
                    "relation": edge["relation"]
                })

        node_df = pd.DataFrame(nodes).drop_duplicates(subset=['id'])
        edge_df = pd.DataFrame(edges).drop_duplicates()
        return node_df, edge_df