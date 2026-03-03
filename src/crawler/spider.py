import json
from huggingface_hub import HfApi
from datetime import datetime

# 定义常见基座模型的标准 ID 映射，用于启发式补全
BASE_MODEL_MAP = {
    "llama-3.1-8b": "meta-llama/Llama-3.1-8B",
    "llama-3-8b": "meta-llama/Meta-Llama-3-8B",
    "llama-3-70b": "meta-llama/Meta-Llama-3-70B",
    "llama-2-7b": "meta-llama/Llama-2-7b-hf",
    "mistral-7b": "mistralai/Mistral-7B-v0.1",
    "mixtral-8x7b": "mistralai/Mixtral-8x7B-v0.1",
    "gpt2": "gpt2",
    "bert-base": "google-bert/bert-base-uncased",
    "stable-diffusion-v1-5": "runwayml/stable-diffusion-v1-5"
}


def is_noise_model(model_id, downloads):
    """
    筛选干扰模型的逻辑：
    1. 关键词过滤：包含 test, internal, dummy, tiny-random 等。
    2. 低活跃度过滤：如果名字包含 tiny 且下载量极低，通常是开发者的临时测试。
    """
    noise_keywords = [
        'test', 'internal', 'dummy', 'tiny-random',
        'tmp', 'temp', 'checkpoints', 'experiment'
    ]
    id_lower = model_id.lower()

    # 规则 1: 命中干扰关键词
    if any(k in id_lower for k in noise_keywords):
        return True

    # 规则 2: 名字里有 tiny 且下载量小于 50 (排除掉像 tiny-llama 这种流行的生产级小模型)
    if 'tiny' in id_lower and downloads < 50:
        return True

    return False


def fetch_enriched_supply_chain(search_term="llama", limit=100):
    api = HfApi()
    print(f"\n>>> 正在抓取 '{search_term}' 相关模型...")

    try:
        models = api.list_models(
            search=search_term,
            sort="downloads",
            direction=-1,
            limit=limit,
            cardData=True
        )
    except Exception as e:
        print(f"访问接口失败: {e}")
        return []

    results = []
    noise_count = 0

    for model in models:
        m_id = model.modelId
        downloads = getattr(model, 'downloads', 0)

        # --- 步骤 0: 干扰过滤 ---
        if is_noise_model(m_id, downloads):
            noise_count += 1
            continue

        tags = getattr(model, 'tags', [])

        # --- 步骤 1: 多级寻找父模型 ---
        parent = None
        # 1.1 从 cardData 字段获取
        if hasattr(model, 'cardData') and model.cardData:
            parent = model.cardData.get('base_model')

        # 1.2 从 tags 列表扫描
        if not parent:
            for tag in tags:
                if tag.startswith("base_model:"):
                    parent = tag.replace("base_model:", "")
                    break

        # 1.3 启发式补全
        is_guess = False
        if not parent:
            id_lower = m_id.lower()
            for key, standard_id in BASE_MODEL_MAP.items():
                if key in id_lower:
                    parent = standard_id
                    is_guess = True
                    break

        # --- 步骤 2: 提取数据集 ---
        datasets = []
        if hasattr(model, 'cardData') and model.cardData:
            ds = model.cardData.get('datasets')
            if isinstance(ds, list):
                datasets.extend(ds)
            elif isinstance(ds, str):
                datasets.append(ds)

        datasets.extend([t.replace("dataset:", "") for t in tags if t.startswith("dataset:")])
        datasets = list(set(datasets))

        # --- 步骤 3: 判定节点类型 (用于定性分析) ---
        # 如果既没有父模型又没有数据集，可能是原始研究项目
        # 如果没有父模型但有数据集，是供应链的源头
        node_type = "derivative"  # 衍生模型
        if not parent:
            node_type = "source_base" if datasets else "standalone"

        results.append({
            "id": m_id,
            "parent_model": parent,
            "node_type": node_type,
            "is_parent_guessed": is_guess,
            "author": model.author,
            "downloads": downloads,
            "likes": getattr(model, 'likes', 0),
            "trending_score": getattr(model, 'trendingScore', 0),
            "last_modified": model.lastModified.isoformat() if model.lastModified else None,
            "datasets": datasets,
            "tags": tags
        })

    print(f"抓取完成。总数: {limit} | 有效节点: {len(results)} | 过滤干扰项: {noise_count}")
    return results


if __name__ == "__main__":
    # 模拟抓取多个主流生态
    search_targets = ["llama-3", "mistral", "qwen"]
    all_data = []

    for term in search_targets:
        all_data.extend(fetch_enriched_supply_chain(term, limit=100))

    # 保存为最终的可视化数据格式
    output_file = "ai_supply_chain_clean.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    # --- 简单的定量统计报告 ---
    print("\n" + "=" * 30)
    print("AI 供应链定量分析简报")
    print("=" * 30)
    print(f"1. 节点总数: {len(all_data)}")

    orphans = [m for m in all_data if not m['parent_model']]
    print(f"2. 供应链源头(无父模型)占比: {len(orphans) / len(all_data):.1%}")

    # 统计影响力最大的基座
    parent_stats = {}
    for m in all_data:
        p = m['parent_model']
        if p:
            parent_stats[p] = parent_stats.get(p, 0) + 1

    top_parents = sorted(parent_stats.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"3. 供应链中最核心的 3 个基座: {top_parents}")
    print(f"数据已保存至: {output_file}")