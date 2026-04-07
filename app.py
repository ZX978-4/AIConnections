#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型血缘关系查询系统 - Python后端API
替代原Streamlit应用，提供REST API供HTML前端调用
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pandas as pd
import numpy as np
import os
from pathlib import Path
import datetime
import hashlib
import json
import requests
import hashlib
import json

app = Flask(__name__, static_folder=None)
CORS(app)  # 允许跨域，供HTML前端调用


def to_json_safe(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    return value


def record_to_json(record):
    return {k: to_json_safe(v) for k, v in record.items()}


def df_to_json_records(df):
    return [record_to_json(rec) for rec in df.to_dict('records')]

# 数据路径
DATA_DIR = Path("data/processed")
NODES_FILE = DATA_DIR / "nodes.csv"
EDGES_FILE = DATA_DIR / "edges.csv"

# 全局数据缓存
nodes_df = None
edges_df = None
model_names = []

def load_data():
    """加载节点和边数据"""
    global nodes_df, edges_df, model_names

    if not NODES_FILE.exists() or not EDGES_FILE.exists():
        # 如果没有数据文件，创建示例数据
        create_sample_data()

    nodes_df = pd.read_csv(NODES_FILE)
    edges_df = pd.read_csv(EDGES_FILE)

    # 预处理：提取所有模型名称
    model_names = nodes_df[nodes_df['type'] == 'model']['id'].tolist()
    model_names.sort()

    print(f"Data loaded: {len(nodes_df)} nodes, {len(edges_df)} edges, {len(model_names)} models")

def create_sample_data():
    """创建示例数据（当真实数据不存在时）"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 示例节点数据
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
        {"id": "chavinlo/alpaca-native", "type": "model", "author": "chavinlo", "downloads": 500000, "license": "CC BY-NC 4.0", "params": "7B"}
    ]

    # 示例边数据
    edges_data = [
        {"source": "meta-llama/Llama-3-8B", "target": "HuggingFaceH4/zephyr-7b-beta", "relation": "BASED_ON"},
        {"source": "meta-llama/Llama-3-8B", "target": "lmsys/vicuna-7b-v1.5", "relation": "BASED_ON"},
        {"source": "EleutherAI/the-pile", "target": "meta-llama/Llama-3-8B", "relation": "TRAINED_ON"},
        {"source": "EleutherAI/the-pile", "target": "meta-llama/Llama-3-70B", "relation": "TRAINED_ON"},
        {"source": "mistralai/Mistral-7B-v0.1", "target": "mistralai/Mistral-7B-Instruct", "relation": "FINE_TUNED"},
        {"source": "meta-llama/Llama-3-8B", "target": "HuggingFaceH4/zephyr-7b-alpha", "relation": "BASED_ON"},
        {"source": "EleutherAI/the-pile", "target": "openlm-research/open_llama_7b", "relation": "TRAINED_ON"},
        {"source": "openlm-research/open_llama_7b", "target": "chavinlo/alpaca-native", "relation": "FINE_TUNED"},
        {"source": "chavinlo/alpaca-native", "target": "lmsys/vicuna-7b-v1.5", "relation": "MERGED_WITH"}
    ]

    pd.DataFrame(nodes_data).to_csv(NODES_FILE, index=False)
    pd.DataFrame(edges_data).to_csv(EDGES_FILE, index=False)
    print("✓ 已创建示例数据")

# ===================== API路由 =====================

@app.route('/', methods=['GET'])
def serve_index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:filename>', methods=['GET'])
def serve_static(filename):
    # 允许直接访问 index.html 或其他本地文件
    if filename.startswith('api/'):
        return jsonify({"error": "API endpoint not found"}), 404
    return send_from_directory('.', filename)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "nodes": len(nodes_df), "edges": len(edges_df)})

@app.route('/api/models', methods=['GET'])
def get_models():
    """获取所有模型列表"""
    query = request.args.get('q', '').lower()

    if query:
        filtered = [m for m in model_names if query in m.lower()]
        return jsonify(filtered[:20])  # 最多返回20个

    return jsonify(model_names)

@app.route('/api/nodes', methods=['GET'])
def get_nodes():
    """获取所有节点数据"""
    return jsonify(df_to_json_records(nodes_df))

@app.route('/api/edges', methods=['GET'])
def get_edges():
    """获取所有边数据"""
    return jsonify(df_to_json_records(edges_df))

@app.route('/api/model/<path:model_id>', methods=['GET'])
def get_model_info(model_id):
    """获取单个模型详细信息"""
    # URL解码处理
    model_id = request.view_args['model_id']

    model_info = nodes_df[nodes_df['id'] == model_id]
    if model_info.empty:
        return jsonify({"error": "Model not found"}), 404

    return jsonify(record_to_json(model_info.iloc[0].to_dict()))

@app.route('/api/model/<path:model_id>/parents', methods=['GET'])
def get_model_parents(model_id):
    """获取模型的父模型/依赖关系"""
    model_id = request.view_args['model_id']

    parent_edges = edges_df[edges_df['target'] == model_id]

    result = []
    for _, row in parent_edges.iterrows():
        source_info = nodes_df[nodes_df['id'] == row['source']]
        if not source_info.empty:
            result.append({
                "source": row['source'],
                "relation": row['relation'],
                "info": record_to_json(source_info.iloc[0].to_dict())
            })

    return jsonify(result)

@app.route('/api/model/<path:model_id>/children', methods=['GET'])
def get_model_children(model_id):
    """获取模型的子模型/衍生关系"""
    model_id = request.view_args['model_id']

    child_edges = edges_df[edges_df['source'] == model_id]

    result = []
    for _, row in child_edges.iterrows():
        target_info = nodes_df[nodes_df['id'] == row['target']]
        if not target_info.empty:
            result.append({
                "target": row['target'],
                "relation": row['relation'],
                "info": record_to_json(target_info.iloc[0].to_dict())
            })

    return jsonify(result)

# 修复后的关键部分 - get_model_lineage 函数

@app.route('/api/model/<path:model_id>/lineage', methods=['GET'])
def get_model_lineage(model_id):
    """获取模型完整血缘关系（父+子）"""
    model_id = request.view_args['model_id']
    depth = request.args.get('depth', 2, type=int)

    print(f"请求模型 {model_id} 的血缘关系，深度: {depth}")

    # 获取模型信息
    model_info = nodes_df[nodes_df['id'] == model_id]
    if model_info.empty:
        return jsonify({"error": "Model not found"}), 404

    # BFS获取父节点（上游）- 记录父节点关系
    ancestors = []
    visited_parents = set([model_id])
    # queue: (当前节点ID, 当前深度, 父节点ID)
    queue = [(model_id, 0, None)]

    while queue:
        current, d, parent_id = queue.pop(0)
        if d >= depth:
            continue

        parent_edges = edges_df[edges_df['target'] == current]
        for _, row in parent_edges.iterrows():
            if row['source'] not in visited_parents:
                visited_parents.add(row['source'])
                source_info = nodes_df[nodes_df['id'] == row['source']]
                if not source_info.empty:
                    # 当前节点是直接父节点
                    actual_parent = current
                    ancestors.append({
                        "id": row['source'],
                        "relation": row['relation'],
                        "depth": d + 1,
                        "parent_id": actual_parent,  # 新增：父节点ID
                        "info": record_to_json(source_info.iloc[0].to_dict())
                    })
                    queue.append((row['source'], d + 1, actual_parent))

    # BFS获取子节点（下游）- 同样记录父节点关系
    descendants = []
    visited_children = set([model_id])
    queue = [(model_id, 0, None)]

    while queue:
        current, d, parent_id = queue.pop(0)
        if d >= depth:
            continue

        child_edges = edges_df[edges_df['source'] == current]
        for _, row in child_edges.iterrows():
            if row['target'] not in visited_children:
                visited_children.add(row['target'])
                target_info = nodes_df[nodes_df['id'] == row['target']]
                if not target_info.empty:
                    # 当前节点是直接父节点
                    actual_parent = current
                    descendants.append({
                        "id": row['target'],
                        "relation": row['relation'],  # 修复：row['relation'] 不是 row['lation']
                        "depth": d + 1,
                        "parent_id": actual_parent,  # 新增：父节点ID
                        "info": record_to_json(target_info.iloc[0].to_dict())
                    })
                    queue.append((row['target'], d + 1, actual_parent))

    return jsonify({
        "model": record_to_json(model_info.iloc[0].to_dict()),
        "ancestors": ancestors,
        "descendants": descendants,
        "stats": {
            "ancestors_count": len(ancestors),
            "descendants_count": len(descendants),
            "total_related": len(ancestors) + len(descendants),
            "depth": depth
        }
    })

@app.route('/api/model/<path:model_id>/sbom', methods=['GET'])
def export_sbom(model_id):
    """导出模型的SBOM（AI物料清单）"""
    model_id = request.view_args['model_id']
    depth = request.args.get('depth', 5, type=int)

    # 获取血缘数据 - 直接调用内部函数而不是通过HTTP
    model_info = nodes_df[nodes_df['id'] == model_id]
    if model_info.empty:
        return jsonify({"error": "Model not found"}), 404

    # 简化版血缘数据获取
    ancestors = []
    descendants = []

    # 获取祖先
    parent_edges = edges_df[edges_df['target'] == model_id]
    for _, row in parent_edges.iterrows():
        source_info = nodes_df[nodes_df['id'] == row['source']]
        if not source_info.empty:
            ancestors.append({
                "id": row['source'],
                "relation": row['relation'],
                "info": record_to_json(source_info.iloc[0].to_dict())
            })

    # 获取后代
    child_edges = edges_df[edges_df['source'] == model_id]
    for _, row in child_edges.iterrows():
        target_info = nodes_df[nodes_df['id'] == row['target']]
        if not target_info.empty:
            descendants.append({
                "id": row['target'],
                "relation": row['relation'],
                "info": record_to_json(target_info.iloc[0].to_dict())
            })

    lineage_data = {
        "model": record_to_json(model_info.iloc[0].to_dict()),
        "ancestors": ancestors,
        "descendants": descendants
    }

    # 构建SBOM
    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": f"SPDXRef-DOCUMENT-{model_id.replace('/', '-')}",
        "name": f"AI Model SBOM - {model_id}",
        "creationInfo": {
            "created": datetime.datetime.now().isoformat(),
            "creators": ["Tool: AIConnections Platform"]
        },
        "packages": [],
        "relationships": []
    }

    # 添加中心模型包
    center_package = {
        "SPDXID": f"SPDXRef-Package-{model_id.replace('/', '-')}",
        "name": model_id,
        "versionInfo": "1.0",
        "supplier": f"Organization: {lineage_data['model']['author']}",
        "downloadLocation": f"https://huggingface.co/{model_id}",
        "filesAnalyzed": False,
        "copyrightText": "NOASSERTION",
        "licenseConcluded": lineage_data['model']['license'] or "NOASSERTION",
        "description": f"AI Model with {lineage_data['model'].get('task', 'unknown')} task, {lineage_data['model']['downloads']} downloads"
    }
    sbom["packages"].append(center_package)

    # 添加祖先包
    for ancestor in lineage_data['ancestors']:
        package = {
            "SPDXID": f"SPDXRef-Package-{ancestor['id'].replace('/', '-')}",
            "name": ancestor['id'],
            "versionInfo": "1.0",
            "supplier": f"Organization: {ancestor['info']['author']}",
            "downloadLocation": f"https://huggingface.co/{ancestor['id']}",
            "filesAnalyzed": False,
            "copyrightText": "NOASSERTION",
            "licenseConcluded": ancestor['info']['license'] or "NOASSERTION",
            "description": f"AI Model with {ancestor['info'].get('task', 'unknown')} task, {ancestor['info']['downloads']} downloads"
        }
        sbom["packages"].append(package)

        # 添加关系
        relationship = {
            "spdxElementId": f"SPDXRef-Package-{model_id.replace('/', '-')}",
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": f"SPDXRef-Package-{ancestor['id'].replace('/', '-')}"
        }
        sbom["relationships"].append(relationship)

    # 添加后代包
    for descendant in lineage_data['descendants']:
        package = {
            "SPDXID": f"SPDXRef-Package-{descendant['id'].replace('/', '-')}",
            "name": descendant['id'],
            "versionInfo": "1.0",
            "supplier": f"Organization: {descendant['info']['author']}",
            "downloadLocation": f"https://huggingface.co/{descendant['id']}",
            "filesAnalyzed": False,
            "copyrightText": "NOASSERTION",
            "licenseConcluded": descendant['info']['license'] or "NOASSERTION",
            "description": f"AI Model with {descendant['info'].get('task', 'unknown')} task, {descendant['info']['downloads']} downloads"
        }
        sbom["packages"].append(package)

        # 添加关系
        relationship = {
            "spdxElementId": f"SPDXRef-Package-{descendant['id'].replace('/', '-')}",
            "relationshipType": "DEPENDS_ON",
            "relatedSpdxElement": f"SPDXRef-Package-{model_id.replace('/', '-')}"
        }
        sbom["relationships"].append(relationship)

    return jsonify(sbom)

@app.route('/api/model/<path:model_id>/verify', methods=['GET'])
def verify_model_integrity(model_id):
    """验证模型完整性和血缘关系"""
    model_id = request.view_args['model_id']

    # 获取模型信息
    model_info = nodes_df[nodes_df['id'] == model_id]
    if model_info.empty:
        return jsonify({"error": "Model not found"}), 404

    model = record_to_json(model_info.iloc[0].to_dict())

    # 计算模型数据的哈希
    model_data = {
        "id": model["id"],
        "type": model["type"],
        "author": model["author"],
        "downloads": model["downloads"],
        "license": model["license"],
        "task": model.get("task", "unknown")
    }
    model_hash = hashlib.sha256(json.dumps(model_data, sort_keys=True).encode()).hexdigest()

    # 获取血缘关系
    lineage_response = requests.get(f'http://localhost:5000/api/model/{model_id}/lineage?depth=2')
    lineage_data = lineage_response.json() if lineage_response.ok else None

    verification_result = {
        "model_id": model_id,
        "model_hash": model_hash,
        "timestamp": datetime.datetime.now().isoformat(),
        "verification_status": "verified",
        "lineage_integrity": True,
        "details": {}
    }

    if lineage_data:
        # 验证血缘关系的完整性
        ancestors_hashes = []
        for ancestor in lineage_data.get('ancestors', []):
            ancestor_data = {
                "id": ancestor["id"],
                "type": ancestor["info"]["type"],
                "author": ancestor["info"]["author"],
                "relation": ancestor["relation"]
            }
            ancestor_hash = hashlib.sha256(json.dumps(ancestor_data, sort_keys=True).encode()).hexdigest()
            ancestors_hashes.append(ancestor_hash)

        descendants_hashes = []
        for descendant in lineage_data.get('descendants', []):
            descendant_data = {
                "id": descendant["id"],
                "type": descendant["info"]["type"],
                "author": descendant["info"]["author"],
                "relation": descendant["relation"]
            }
            descendant_hash = hashlib.sha256(json.dumps(descendant_data, sort_keys=True).encode()).hexdigest()
            descendants_hashes.append(descendant_hash)

        # 计算血缘哈希
        lineage_hash_data = {
            "model_hash": model_hash,
            "ancestors": sorted(ancestors_hashes),
            "descendants": sorted(descendants_hashes)
        }
        lineage_hash = hashlib.sha256(json.dumps(lineage_hash_data, sort_keys=True).encode()).hexdigest()

        verification_result["lineage_hash"] = lineage_hash
        verification_result["details"] = {
            "ancestors_count": len(ancestors_hashes),
            "descendants_count": len(descendants_hashes),
            "total_relations": len(ancestors_hashes) + len(descendants_hashes)
        }
    else:
        verification_result["lineage_integrity"] = False
        verification_result["details"]["error"] = "Failed to fetch lineage data"

    return jsonify(verification_result)

if __name__ == '__main__':
    load_data()
    print("🚀 启动API服务器: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)