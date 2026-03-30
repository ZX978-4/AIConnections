import requests
from src.utils.common import logger


class HFWebParser:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def get_model_relationships(self, model_id: str):
        """获取下游模型：Adapters, Finetunes, Quantizations"""
        results = {"downstream": []}
        search_url = "https://huggingface.co/api/models"

        # 模拟查询：哪些模型的 base_model 是当前 model_id
        params = {
            "filter": f"base_model:{model_id}",
            "sort": "downloads",
            "direction": -1,
            "limit": 100
        }

        try:
            resp = requests.get(search_url, params=params, headers=self.headers, timeout=10)
            if resp.status_code == 200:
                for m in resp.json():
                    m_id = m.get('id')
                    tags = [t.lower() for t in m.get('tags', [])]

                    # 识别子类类型
                    rel_type = "fine-tune"
                    if "adapter" in tags or "lora" in tags:
                        rel_type = "adapter"
                    elif any(q in tags for q in ["gguf", "awq", "gptq", "exl2"]):
                        rel_type = "quantization"

                    results["downstream"].append({"id": m_id, "type": rel_type})
            logger.info(f"  Found {len(results['downstream'])} downstream models for {model_id}")
        except Exception as e:
            logger.error(f"Web API error for {model_id}: {e}")

        return results