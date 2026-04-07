import time

import requests

from src.utils.common import logger


class HFWebParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
        )

    def _safe_get(self, url, params, max_retries=3):
        """GET with exponential backoff."""
        for i in range(max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=15)
                if resp.status_code == 200:
                    return resp
                if resp.status_code == 429:
                    wait = (2**i) + 2
                    logger.warning(f"Rate limit hit. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {resp.status_code} error for {url}")
                    break
            except Exception as e:
                wait = (2**i) + 1
                logger.warning(f"Connection error: {e}. Retrying in {wait}s...")
                time.sleep(wait)
        return None

    def get_model_relationships(self, model_id: str, limit: int = 10):
        results = {"downstream": []}
        search_url = "https://huggingface.co/api/models"

        params = {
            "filter": f"base_model:{model_id}",
            "sort": "downloads",
            "direction": -1,
            "limit": limit,
        }

        resp = self._safe_get(search_url, params)
        if resp:
            for m in resp.json():
                m_id = m.get("id", "").lower()
                tags = [t.lower() for t in m.get("tags", [])]

                rel_type = "fine-tune"

                if any(x in tags for x in ["adapter", "lora", "peft"]):
                    rel_type = "adapter"
                elif any(q in tags for q in ["gguf", "awq", "gptq", "exl2"]) or any(
                    q in m_id for q in ["-gguf", "-awq", "-gptq", "-exl2"]
                ):
                    rel_type = "quantization"
                elif "merge" in tags or "mergekit" in tags or "merged" in m_id:
                    rel_type = "merge"
                elif "distill" in tags or "distilled" in tags or "distill" in m_id:
                    rel_type = "distillation"
                elif "moe" in tags or "moe" in m_id:
                    rel_type = "moe"

                results["downstream"].append({"id": m.get("id"), "type": rel_type})

        return results
