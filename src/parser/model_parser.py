import requests
from src.utils.common import logger


class HFWebParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def get_model_relationships(self, model_id: str, limit: int = 10):
        results = {"downstream": []}
        search_url = "https://huggingface.co/api/models"

        params = {
            "filter": f"base_model:{model_id}",
            "sort": "downloads",
            "direction": -1,
            "limit": limit
        }

        try:
            resp = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                for m in resp.json():
                    m_id = m.get('id', '').lower()
                    tags = [t.lower() for t in m.get('tags', [])]

                    # --- 增强版关系识别逻辑 ---
                    rel_type = "fine-tune"  # 默认类型

                    # 1. 适配器识别 (Adapters/LoRA)
                    if "adapter" in tags or "lora" in tags or "peft" in tags:
                        rel_type = "adapter"

                    # 2. 量化版本识别 (Quantization)
                    elif any(q in tags for q in ["gguf", "awq", "gptq", "exl2"]) or \
                            any(q in m_id for q in ["-gguf", "-awq", "-gptq"]):
                        rel_type = "quantization"

                    # 3. 合并模型识别 (Model Merging)
                    elif "merge" in tags or "mergekit" in tags or "merged" in m_id:
                        rel_type = "merge"

                    # 4. 蒸馏模型识别 (Distillation)
                    elif "distill" in tags or "distilled" in tags or "distill" in m_id:
                        rel_type = "distillation"

                    # 5. 混合专家模型识别 (Mixture of Experts - 结构演进)
                    elif "moe" in tags or "moe" in m_id:
                        rel_type = "moe"

                    results["downstream"].append({"id": m.get('id'), "type": rel_type})

        except Exception as e:
            logger.error(f"Web API error for {model_id}: {e}")

        return results