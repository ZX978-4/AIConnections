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
import requests
import urllib.parse as urllib
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

@app.route('/api/model/<path:model_id>/license_check', methods=['GET'])
def model_license_check(model_id):
    """Check model license against upstream licenses for obvious conflicts.
    Returns JSON with model_license, upstream (list of {id, license, conflict}), and conflicts (list of strings).
    Uses simple heuristics: if model license is 'proprietary' or contains 'non-commercial' then flag upstream permissive licenses that allow commercial use as potential mismatch, and flag GPL-style copyleft vs permissive contradictions.
    """
    model_id = request.view_args['model_id']

    # find model row
    row = nodes_df[nodes_df['id'] == model_id]
    if row.empty:
        return jsonify({'status': 'error', 'message': 'Model not found'}), 404

    model_rec = record_to_json(row.iloc[0].to_dict())
    model_license = (model_rec.get('license') or '').strip()

    # BFS upstream to collect ancestors' licenses
    visited = set([model_id])
    queue = [model_id]
    upstream = []

    while queue:
        cur = queue.pop(0)
        parent_edges = edges_df[edges_df['target'] == cur]
        for _, r in parent_edges.iterrows():
            src = r['source']
            if src in visited: continue
            visited.add(src)
            src_info = nodes_df[nodes_df['id'] == src]
            if src_info.empty:
                continue
            rec = record_to_json(src_info.iloc[0].to_dict())
            upstream.append({'id': src, 'license': rec.get('license')})
            queue.append(src)
    
    # 如果是源头节点（没有上游依赖），直接返回没问题
    if not upstream:
        return jsonify({
            'status': 'ok',
            'model_license': model_license or 'unknown',
            'upstream': [],
            'conflicts': []
        })

    # simple compatibility rules (heuristic):
    # - If model license contains 'non-commercial' or 'nc' -> warn if upstream license is permissive that allows commercial use
    # - If model license is permissive (MIT, Apache) and upstream is copyleft (GPL, AGPL) -> conflict (since derived work may need to be copyleft)
    # - If model license is closed/proprietary and upstream is copyleft -> conflict
    def _norm(lic):
        if not lic: return ''
        return lic.lower()

    mnorm = _norm(model_license)
    conflicts = []
    result_up = []

    for u in upstream:
        un = _norm(u.get('license') or '')
        conflict = False
        # detect copyleft
        is_copyleft = any(k in un for k in ['gpl', 'agpl', 'lgpl', 'copyleft'])
        is_nc = 'non' in un and 'commercial' in un or 'nc' in un
        is_proprietary = any(k in un for k in ['proprietary', 'closed']) or un == 'commercial'

        # treat unknown/empty or ambiguous upstream license as potential conflict (report explicitly)
        if not un or 'unknown' in un or 'other' in un:
            conflict = True
            if not un:
                conflicts.append(f"上游 {u['id']} 模型许可为空")
            else:
                conflicts.append(f"上游 {u['id']} 模型许可为 '{u.get('license')}'（unknown/other），标记为隐患")

        if mnorm:
            # model is non-commercial
            if ('non' in mnorm and 'commercial' in mnorm) or 'nc' in mnorm:
                if not is_nc:
                    conflict = True
                    conflicts.append(f"模型许可要求非商业，但上游 {u['id']} 许可为 {u.get('license')}")
            # model is permissive but upstream copyleft
            if any(k in mnorm for k in ['mit', 'apache', 'bsd', 'permissive']) and is_copyleft:
                conflict = True
                conflicts.append(f"模型许可 {model_license} 可能与上游 {u['id']} 的 copyleft 许可 {u.get('license')} 冲突")
            # model proprietary vs upstream copyleft
            if any(k in mnorm for k in ['proprietary', 'closed']) and is_copyleft:
                conflict = True
                conflicts.append(f"闭源模型可能无法包含上游 {u['id']} 的 copyleft 代码许可 {u.get('license')}")

    # keep original license as-is (may be None) and mark conflict
    result_up.append({**u, 'conflict': conflict})

    status = 'ok' if not conflicts else 'conflicts'

    return jsonify({
        'status': status,
        'model_license': model_license or 'unknown',
        'upstream': result_up,
        'conflicts': conflicts
    })

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

def pre_check_risk(model_id):
    """预检模型风险等级
    
    根据风险充分条件表检查模型风险，优先检查元数据
    如果满足任何一个充分条件，立即返回风险等级和原因
    
    Args:
        model_id: 模型ID
    
    Returns:
        dict: 包含风险等级和原因的字典
    """
    # 模拟获取模型的详细信息，实际应用中可能需要从数据库或API获取
    model_info = nodes_df[nodes_df['id'] == model_id]
    if model_info.empty:
        return {"error": "Model not found"}
    
    model_rec = record_to_json(model_info.iloc[0].to_dict())
    
    # 模拟元数据和检测报告数据
    # 实际应用中，这些数据可能需要从其他服务或数据库获取
    metadata = {
        "author_unverified": False,  # 假设默认作者已验证
        "is_hot_model_name_clone": False,  # 假设默认不是热门模型名称克隆
        "has_pickle_files": False,  # 假设默认没有pickle文件
        "has_safetensors": True,  # 假设默认有safetensors文件
        "trust_remote_code": False,  # 假设默认不信任远程代码
        "json": {"status": "safe"}  # 假设默认检测报告状态为安全
    }
    
    # 优先检查元数据
    # 1. 检查检测报告状态
    if metadata.get("json", {}).get("status") == "unsafe":
        return {
            "risk_level": "🔴 INFECTED",
            "reason": "检测报告显示模型不安全"
        }
    
    # 2. 检查文件格式风险
    if metadata.get("has_pickle_files") and not metadata.get("has_safetensors"):
        return {
            "risk_level": "🟠 HIGH RISK",
            "reason": "模型包含pickle文件但不包含safetensors文件，格式高危"
        }
    
    # 3. 检查加载方式风险
    if metadata.get("trust_remote_code"):
        return {
            "risk_level": "🟠 HIGH RISK",
            "reason": "模型信任远程代码，逻辑不可控"
        }
    
    # 4. 检查元数据风险
    if metadata.get("author_unverified") and metadata.get("is_hot_model_name_clone"):
        return {
            "risk_level": "🟡 SUSPICIOUS",
            "reason": "作者未验证且模型名称疑似热门模型克隆，身份可疑"
        }
    
    # 无风险
    return {
        "risk_level": "🟢 SAFE",
        "reason": "模型通过所有安全检查"
    }


@app.route('/api/model/<path:model_id>/risk_check', methods=['GET'])
def model_risk_check(model_id):
    """检查模型风险等级"""
    model_id = request.view_args['model_id']
    result = pre_check_risk(model_id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取全局统计数据"""
    relation_counts = edges_df['relation'].value_counts().to_dict()

    return jsonify({
        "total_nodes": len(nodes_df),
        "total_edges": len(edges_df),
        "model_count": len(nodes_df[nodes_df['type'] == 'model']),
        "dataset_count": len(nodes_df[nodes_df['type'] == 'dataset']),
        "relation_distribution": relation_counts
    })

if __name__ == '__main__':
    load_data()
    print("🚀 启动API服务器: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)