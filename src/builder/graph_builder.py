# src/builder/graph_builder.py
import pandas as pd


class SupplyChainBuilder:
    def __init__(self, model_data, dataset_data):
        self.model_data = model_data
        self.dataset_data = dataset_data

    def process(self):
        nodes, edges = [], []

        for mid, info in self.model_data.items():
            if "author" in info:
                nodes.append(
                    {
                        "id": mid,
                        "type": "model",
                        "task": info.get("task", "unknown"),
                        "downloads": info.get("downloads", 0),
                        "author": info.get("author", "unknown"),
                        "license": info.get("license", "unknown"),
                    }
                )

            for e in info.get("edges", []):
                edges.append({"source": mid, "target": e["to"], "relation": e["relation"]})

            for ds_id in info.get("datasets", []):
                edges.append({"source": ds_id, "target": mid, "relation": "trained_on"})

        for did, dinfo in self.dataset_data.items():
            nodes.append(
                {
                    "id": did,
                    "type": "dataset",
                    "downloads": dinfo.get("downloads", 0),
                    "author": dinfo.get("author", "unknown"),
                    "license": dinfo.get("license", "unknown"),
                }
            )

        return pd.DataFrame(nodes).drop_duplicates("id"), pd.DataFrame(edges).drop_duplicates()
