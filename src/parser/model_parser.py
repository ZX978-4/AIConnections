import requests
import time
from src.utils.common import logger

class HFWebParser:
    def __init__(self):
        # 使用 Session 复用 TCP 连接，提高稳定性
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        })

    def _safe_get(self, url, params, max_retries=3):
        """带有指数退避逻辑的健壮请求函数"""
        for i in range(max_retries):
            try:
                resp = self.session.get(url, params=params, timeout=15)
                if resp.status_code == 200:
                    return resp
                elif resp.status_code == 429:  # 触发速率限制
                    wait = (2 ** i) + 2
                    logger.warning(f"Rate limit hit. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    logger.error(f"HTTP {resp.status_code} error for {url}")
                    break
            except Exception as e:
                wait = (2 ** i) + 1
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
            "limit": limit
        }

        resp = self._safe_get(search_url, params)
        if resp:
            for m in resp.json():
                m_id = m.get('id', '').lower()
                tags = [t.lower() for t in m.get('tags', [])]

                # --- 增强版多维度关系识别逻辑 ---
                rel_type = "fine-tune"  # 默认

                # 1. 适配器识别
                if any(x in tags for x in ["adapter", "lora", "peft"]):
                    rel_type = "adapter"

                # 2. 量化版本识别 (增加 exl2, bitsandbytes 识别)
                elif any(q in tags for q in ["gguf", "awq", "gptq", "exl2"]) or \
                     any(q in m_id for q in ["-gguf", "-awq", "-gptq", "-exl2"]):
                    rel_type = "quantization"

                # 3. 合并模型识别 (识别 Mergekit 产物)
                elif "merge" in tags or "mergekit" in tags or "merged" in m_id:
                    rel_type = "merge"

                # 4. 蒸馏模型识别 (识别教师-学生模型关系)
                elif "distill" in tags or "distilled" in tags or "distill" in m_id:
                    rel_type = "distillation"

                # 5. 混合专家模型识别
                elif "moe" in tags or "moe" in m_id:
                    rel_type = "moe"

                results["downstream"].append({"id": m.get('id'), "type": rel_type})

        return results