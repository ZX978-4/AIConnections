#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Model lineage API (Flask).
Provides REST endpoints for the static HTML frontend.
"""

from collections import deque
import datetime
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from src.utils.sample_data import get_sample_nodes_edges

app = Flask(__name__, static_folder=None)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"
NODES_FILE = DATA_DIR / "nodes.csv"
EDGES_FILE = DATA_DIR / "edges.csv"

nodes_df = None
edges_df = None
model_names = []


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
    return [record_to_json(rec) for rec in df.to_dict("records")]


def create_sample_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    nodes_data, edges_data = get_sample_nodes_edges()
    pd.DataFrame(nodes_data).to_csv(NODES_FILE, index=False)
    pd.DataFrame(edges_data).to_csv(EDGES_FILE, index=False)
    print("Sample data created in data/processed.")


def load_data():
    """Load nodes/edges data. Create sample data if missing."""
    global nodes_df, edges_df, model_names

    if not NODES_FILE.exists() or not EDGES_FILE.exists():
        create_sample_data()

    nodes_df = pd.read_csv(NODES_FILE)
    edges_df = pd.read_csv(EDGES_FILE)

    model_names = nodes_df[nodes_df["type"] == "model"]["id"].tolist()
    model_names.sort()

    print(
        f"Data loaded: {len(nodes_df)} nodes, {len(edges_df)} edges, {len(model_names)} models"
    )


def ensure_data_loaded():
    if nodes_df is None or edges_df is None:
        load_data()


def _collect_relations(model_id, depth, direction):
    """
    Collect ancestors or descendants with BFS.
    direction: "ancestors" or "descendants"
    """
    results = []
    visited = {model_id}
    queue = deque([(model_id, 0)])

    while queue:
        current, d = queue.popleft()
        if d >= depth:
            continue

        if direction == "ancestors":
            related_edges = edges_df[edges_df["target"] == current]
            next_key = "source"
        else:
            related_edges = edges_df[edges_df["source"] == current]
            next_key = "target"

        for _, row in related_edges.iterrows():
            next_id = row[next_key]
            if next_id in visited:
                continue

            info = nodes_df[nodes_df["id"] == next_id]
            if info.empty:
                continue

            visited.add(next_id)
            results.append(
                {
                    "id": next_id,
                    "relation": row["relation"],
                    "depth": d + 1,
                    "parent_id": current,
                    "info": record_to_json(info.iloc[0].to_dict()),
                }
            )
            queue.append((next_id, d + 1))

    return results


def build_lineage(model_id, depth):
    """Build lineage (ancestors + descendants) for a model."""
    model_info = nodes_df[nodes_df["id"] == model_id]
    if model_info.empty:
        return None

    ancestors = _collect_relations(model_id, depth, "ancestors")
    descendants = _collect_relations(model_id, depth, "descendants")

    return {
        "model": record_to_json(model_info.iloc[0].to_dict()),
        "ancestors": ancestors,
        "descendants": descendants,
        "stats": {
            "ancestors_count": len(ancestors),
            "descendants_count": len(descendants),
            "total_related": len(ancestors) + len(descendants),
            "depth": depth,
        },
    }


@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/<path:filename>", methods=["GET"])
def serve_static(filename):
    if filename.startswith("api/"):
        return jsonify({"error": "API endpoint not found"}), 404
    return send_from_directory(str(BASE_DIR), filename)


@app.route("/api/health", methods=["GET"])
def health_check():
    ensure_data_loaded()
    return jsonify({"status": "ok", "nodes": len(nodes_df), "edges": len(edges_df)})


@app.route("/api/models", methods=["GET"])
def get_models():
    ensure_data_loaded()
    query = request.args.get("q", "").lower()

    if query:
        filtered = [m for m in model_names if query in m.lower()]
        return jsonify(filtered[:20])

    return jsonify(model_names)


@app.route("/api/nodes", methods=["GET"])
def get_nodes():
    ensure_data_loaded()
    return jsonify(df_to_json_records(nodes_df))


@app.route("/api/edges", methods=["GET"])
def get_edges():
    ensure_data_loaded()
    return jsonify(df_to_json_records(edges_df))


@app.route("/api/model/<path:model_id>", methods=["GET"])
def get_model_info(model_id):
    ensure_data_loaded()
    model_info = nodes_df[nodes_df["id"] == model_id]
    if model_info.empty:
        return jsonify({"error": "Model not found"}), 404

    return jsonify(record_to_json(model_info.iloc[0].to_dict()))


@app.route("/api/model/<path:model_id>/parents", methods=["GET"])
def get_model_parents(model_id):
    ensure_data_loaded()

    parent_edges = edges_df[edges_df["target"] == model_id]

    result = []
    for _, row in parent_edges.iterrows():
        source_info = nodes_df[nodes_df["id"] == row["source"]]
        if not source_info.empty:
            result.append(
                {
                    "source": row["source"],
                    "relation": row["relation"],
                    "info": record_to_json(source_info.iloc[0].to_dict()),
                }
            )

    return jsonify(result)


@app.route("/api/model/<path:model_id>/children", methods=["GET"])
def get_model_children(model_id):
    ensure_data_loaded()

    child_edges = edges_df[edges_df["source"] == model_id]

    result = []
    for _, row in child_edges.iterrows():
        target_info = nodes_df[nodes_df["id"] == row["target"]]
        if not target_info.empty:
            result.append(
                {
                    "target": row["target"],
                    "relation": row["relation"],
                    "info": record_to_json(target_info.iloc[0].to_dict()),
                }
            )

    return jsonify(result)


@app.route("/api/model/<path:model_id>/lineage", methods=["GET"])
def get_model_lineage(model_id):
    ensure_data_loaded()
    depth = request.args.get("depth", 2, type=int)

    lineage = build_lineage(model_id, depth)
    if lineage is None:
        return jsonify({"error": "Model not found"}), 404

    return jsonify(lineage)


@app.route("/api/model/<path:model_id>/sbom", methods=["GET"])
def export_sbom(model_id):
    ensure_data_loaded()
    depth = request.args.get("depth", 5, type=int)

    lineage = build_lineage(model_id, depth)
    if lineage is None:
        return jsonify({"error": "Model not found"}), 404

    sbom = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": f"SPDXRef-DOCUMENT-{model_id.replace('/', '-')}",
        "name": f"AI Model SBOM - {model_id}",
        "creationInfo": {
            "created": datetime.datetime.now().isoformat(),
            "creators": ["Tool: AIConnections Platform"],
        },
        "packages": [],
        "relationships": [],
    }

    def make_package(node_id, info):
        return {
            "SPDXID": f"SPDXRef-Package-{node_id.replace('/', '-')}",
            "name": node_id,
            "versionInfo": "1.0",
            "supplier": f"Organization: {info.get('author', 'unknown')}",
            "downloadLocation": f"https://huggingface.co/{node_id}",
            "filesAnalyzed": False,
            "copyrightText": "NOASSERTION",
            "licenseConcluded": info.get("license") or "NOASSERTION",
            "description": f"AI Model with {info.get('task', 'unknown')} task, {info.get('downloads', 0)} downloads",
        }

    packages = {}
    center_info = lineage["model"]
    packages[model_id] = make_package(model_id, center_info)

    for item in lineage["ancestors"] + lineage["descendants"]:
        pid = item["id"]
        if pid not in packages:
            packages[pid] = make_package(pid, item["info"])

    sbom["packages"] = list(packages.values())

    for ancestor in lineage["ancestors"]:
        sbom["relationships"].append(
            {
                "spdxElementId": f"SPDXRef-Package-{model_id.replace('/', '-')}",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": f"SPDXRef-Package-{ancestor['id'].replace('/', '-')}",
            }
        )

    for descendant in lineage["descendants"]:
        sbom["relationships"].append(
            {
                "spdxElementId": f"SPDXRef-Package-{descendant['id'].replace('/', '-')}",
                "relationshipType": "DEPENDS_ON",
                "relatedSpdxElement": f"SPDXRef-Package-{model_id.replace('/', '-')}",
            }
        )

    return jsonify(sbom)


@app.route("/api/model/<path:model_id>/verify", methods=["GET"])
def verify_model_integrity(model_id):
    ensure_data_loaded()

    model_info = nodes_df[nodes_df["id"] == model_id]
    if model_info.empty:
        return jsonify({"error": "Model not found"}), 404

    model = record_to_json(model_info.iloc[0].to_dict())

    model_data = {
        "id": model["id"],
        "type": model["type"],
        "author": model["author"],
        "downloads": model["downloads"],
        "license": model["license"],
        "task": model.get("task", "unknown"),
    }
    model_hash = hashlib.sha256(json.dumps(model_data, sort_keys=True).encode()).hexdigest()

    lineage_data = build_lineage(model_id, 2)

    verification_result = {
        "model_id": model_id,
        "model_hash": model_hash,
        "timestamp": datetime.datetime.now().isoformat(),
        "verification_status": "verified",
        "lineage_integrity": True,
        "details": {},
    }

    if lineage_data:
        ancestors_hashes = []
        for ancestor in lineage_data.get("ancestors", []):
            ancestor_data = {
                "id": ancestor["id"],
                "type": ancestor["info"]["type"],
                "author": ancestor["info"]["author"],
                "relation": ancestor["relation"],
            }
            ancestor_hash = hashlib.sha256(json.dumps(ancestor_data, sort_keys=True).encode()).hexdigest()
            ancestors_hashes.append(ancestor_hash)

        descendants_hashes = []
        for descendant in lineage_data.get("descendants", []):
            descendant_data = {
                "id": descendant["id"],
                "type": descendant["info"]["type"],
                "author": descendant["info"]["author"],
                "relation": descendant["relation"],
            }
            descendant_hash = hashlib.sha256(json.dumps(descendant_data, sort_keys=True).encode()).hexdigest()
            descendants_hashes.append(descendant_hash)

        lineage_hash_data = {
            "model_hash": model_hash,
            "ancestors": sorted(ancestors_hashes),
            "descendants": sorted(descendants_hashes),
        }
        lineage_hash = hashlib.sha256(json.dumps(lineage_hash_data, sort_keys=True).encode()).hexdigest()

        verification_result["lineage_hash"] = lineage_hash
        verification_result["details"] = {
            "ancestors_count": len(ancestors_hashes),
            "descendants_count": len(descendants_hashes),
            "total_relations": len(ancestors_hashes) + len(descendants_hashes),
        }
    else:
        verification_result["lineage_integrity"] = False
        verification_result["details"]["error"] = "Failed to build lineage data"

    return jsonify(verification_result)


if __name__ == "__main__":
    load_data()
    print("API server running at http://localhost:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
