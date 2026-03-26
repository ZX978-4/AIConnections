from huggingface_hub import HfApi
import json

def get_detailed_models(limit=100):
    api = HfApi()
    models = api.list_models(
        sort="downloads",
        direction=-1,
        limit=limit,
        full=True,
        fetch_config=True,
    )

    detailed_data = []
    for m in models:
        params = None
        if hasattr(m, 'safetensors') and m.safetensors:
            params = m.safetensors.get("parameters", {}).get("total", None)

        info = {
            "基本身份": {
                "model_id": m.id,
                "author": m.author,
                "created_at": m.created_at.isoformat() if hasattr(m, 'created_at') and m.created_at else None,
                "sha": m.sha,
            },
            "供应链血缘": {
                # "base_model": getattr(m.card_data, "base_model", None) if m.card_data else None,
                "base_model": m.card_data.get("base_model", "无") if m.card_data else "无",
                "datasets": getattr(m.card_data, "datasets", []) if m.card_data else [],
                "is_merged": "merge" in (m.tags or []),
                "is_quantized": any(t in (m.tags or []) for t in ["gguf", "awq", "gptq"]),
                "tags": m.tags,
            },
            "技术规格": {
                "architecture": m.config.get("model_type") if m.config else None,
                "parameters_total": params,
                "pipeline_tag": m.pipeline_tag,
                "library_name": m.library_name,
            },
            "社区与影响力": {
                "downloads": m.downloads,
                "likes": m.likes,
                "trending_score": getattr(m, "trendingScore", 0),
            },
            "合规与文件": {
                "license": getattr(m.card_data, "license", "unknown") if m.card_data else "unknown",
                "files": [f.rfilename for f in m.siblings],
                "private": m.private,
            }
        }
        detailed_data.append(info)
    return detailed_data


if __name__ == "__main__":
    data = get_detailed_models(100)
    with open("models_output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
