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
        # 使用动态传入的 limit
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
                    m_id = m.get('id')
                    tags = [t.lower() for t in m.get('tags', [])]
                    rel_type = "fine-tune"
                    if "adapter" in tags or "lora" in tags: rel_type = "adapter"
                    elif any(q in tags for q in ["gguf", "awq", "gptq"]): rel_type = "quantization"
                    results["downstream"].append({"id": m_id, "type": rel_type})
        except Exception as e:
            logger.error(f"Web API error for {model_id}: {e}")
        return results