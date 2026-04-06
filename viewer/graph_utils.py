import networkx as nx
import streamlit as st


def get_all_descendants(G, start_node, max_depth=10):
    if start_node not in G:
        return set()

    descendants = set()
    visited = {start_node}
    queue = [(start_node, 0)]

    while queue:
        current_node, current_depth = queue.pop(0)
        if current_depth >= max_depth:
            continue

        children = list(G.successors(current_node))
        for child in children:
            if child not in visited:
                visited.add(child)
                descendants.add(child)
                queue.append((child, current_depth + 1))

    return descendants


def get_all_ancestors(G, start_node, max_depth=10):
    if start_node not in G:
        return set()

    ancestors = set()
    visited = {start_node}
    queue = [(start_node, 0)]

    while queue:
        current_node, current_depth = queue.pop(0)
        if current_depth >= max_depth:
            continue

        parents = list(G.predecessors(current_node))
        for parent in parents:
            if parent not in visited:
                visited.add(parent)
                ancestors.add(parent)
                queue.append((parent, current_depth + 1))

    return ancestors


@st.cache_data
def build_local_graph(center_model, edges_df, node_ids_set, node_info, max_depth=1, include_ancestors=True, include_descendants=True):
    G = nx.DiGraph()
    if center_model not in node_ids_set:
        return G

    visited = {center_model}
    queue = [(center_model, 0)]
    G.add_node(center_model, **node_info[center_model])

    while queue:
        current_node, current_depth = queue.pop(0)
        if current_depth >= max_depth:
            continue

        if include_ancestors:
            parent_edges = edges_df[edges_df['target'] == current_node]
            for _, row in parent_edges.iterrows():
                parent_id = row['source']
                if parent_id in node_ids_set:
                    G.add_edge(parent_id, current_node, relation=row['relation'])
                    if parent_id not in visited:
                        visited.add(parent_id)
                        queue.append((parent_id, current_depth + 1))
                        G.add_node(parent_id, **node_info[parent_id])

        if include_descendants:
            child_edges = edges_df[edges_df['source'] == current_node]
            for _, row in child_edges.iterrows():
                child_id = row['target']
                if child_id in node_ids_set:
                    G.add_edge(current_node, child_id, relation=row['relation'])
                    if child_id not in visited:
                        visited.add(child_id)
                        queue.append((child_id, current_depth + 1))
                        G.add_node(child_id, **node_info[child_id])

    return G


@st.cache_data
def build_lineage_chain_graph(center_model, edges_df, node_ids_set, node_info, direction="both"):
    G = nx.DiGraph()
    if center_model not in node_ids_set:
        return G

    full_G = nx.DiGraph()
    for _, row in edges_df.iterrows():
        if row['source'] in node_ids_set and row['target'] in node_ids_set:
            full_G.add_edge(row['source'], row['target'], relation=row['relation'])

    related_nodes = {center_model}
    if direction in ["both", "ancestors"]:
        related_nodes.update(get_all_ancestors(full_G, center_model))
    if direction in ["both", "descendants"]:
        related_nodes.update(get_all_descendants(full_G, center_model))

    for node_id in related_nodes:
        if node_id in node_info:
            G.add_node(node_id, **node_info[node_id])

    for _, row in edges_df.iterrows():
        if row['source'] in related_nodes and row['target'] in related_nodes:
            G.add_edge(row['source'], row['target'], relation=row['relation'])

    return G


@st.cache_data
def build_full_graph(edges_df, node_ids_set, node_info, max_nodes=5000):
    G = nx.DiGraph()
    all_nodes = list(node_ids_set)
    if len(all_nodes) > max_nodes:
        st.warning(f"节点数超过{max_nodes}，已自动采样避免渲染卡顿")
        all_nodes = all_nodes[:max_nodes]

    for node_id in all_nodes:
        G.add_node(node_id, **node_info[node_id])

    for _, row in edges_df.iterrows():
        if row['source'] in all_nodes and row['target'] in all_nodes:
            G.add_edge(row['source'], row['target'], relation=row['relation'])

    return G
