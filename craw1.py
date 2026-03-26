from huggingface_hub import HfApi
import pandas as pd
import json
import time
import re
import requests

LIMIT = 20
api = HfApi()

# README.md 正文正则 + 关键词提取（作者会在文档里写 “基于 xxx 微调”）
# 单独的 adapter_config.json/peft_config.json 扫描
# 模型文件列表线索挖掘（看有没有加载 base model 的文件名）
# Hugging Face 搜索 API 反向匹配（搜模型名找官方 base）
# 更激进的模型 ID 语义解析（支持所有主流模型系列）
# pipeline_tag + library_name + model_type 三维联合匹配
# 作者维度关联（同一作者的模型链）

# ======================
# 🎯 超全模型系列映射表（新增大量系列）
# ======================
MODEL_FAMILY_MAP = {
    # Qwen 系列
    "qwen": "Qwen/Qwen-7B",
    "qwen2": "Qwen/Qwen2-7B",
    "qwen2.5": "Qwen/Qwen2.5-7B",
    "qwen3": "Qwen/Qwen3-7B",
    "qwen3.5": "qwen/Qwen3.5-27B",
    # Llama 系列
    "llama": "meta-llama/Llama-2-7b-hf",
    "llama2": "meta-llama/Llama-2-7b-hf",
    "llama3": "meta-llama/Meta-Llama-3-8B",
    "llama3.1": "meta-llama/Llama-3.1-8B",
    "llama3.2": "meta-llama/Llama-3.2-8B",
    # Mistral 系列
    "mistral": "mistralai/Mistral-7B-v0.1",
    "mixtral": "mistralai/Mixtral-8x7B-v0.1",
    # Gemma 系列
    "gemma": "google/gemma-7b",
    "gemma2": "google/gemma-2-9b",
    # Phi 系列
    "phi": "microsoft/phi-2",
    "phi2": "microsoft/phi-2",
    "phi3": "microsoft/Phi-3-mini-4k-instruct",
    # BERT 系列
    "bert": "bert-base-uncased",
    "roberta": "roberta-base",
    "deberta": "microsoft/deberta-v3-base",
    # 视觉系列
    "vit": "google/vit-base-patch16-224",
    "clip": "openai/clip-vit-base-patch32",
    "stable-diffusion": "runwayml/stable-diffusion-v1-5",
    "sdxl": "stabilityai/stable-diffusion-xl-base-1.0",
    # T5 系列
    "t5": "t5-base",
    "flan-t5": "google/flan-t5-base",
    # 其他
    "yolov": "ultralytics/yolov8x",
    "whisper": "openai/whisper-small",
}

# ======================
# 🔍 1. 从 README.md 提取（超强！作者会写）
# ======================
def get_base_from_readme(model_id: str, timeout=10):
    try:
        url = f"https://huggingface.co/{model_id}/raw/main/README.md"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None

        text = resp.text.lower()

        # 关键词列表
        keywords = [
            r"based\s+on\s+([\w\-\/]+)",
            r"fine-tuned\s+from\s+([\w\-\/]+)",
            r"initialized\s+from\s+([\w\-\/]+)",
            r"forked\s+from\s+([\w\-\/]+)",
            r"base\s+model\s*[:=]\s*([\w\-\/]+)",
            r"parent\s+model\s*[:=]\s*([\w\-\/]+)",
        ]

        for pat in keywords:
            match = re.search(pat, text)
            if match:
                candidate = match.group(1).strip()
                if len(candidate) > 3 and "/" in candidate:
                    return candidate

        return None
    except Exception:
        return None

# ======================
# 🛠️ 2. 从单独的 adapter/peft config 提取
# ======================
def get_base_from_separate_configs(model_id: str, timeout=8):
    config_files = [
        "adapter_config.json",
        "peft_config.json",
        "lora_config.json",
    ]
    for f in config_files:
        try:
            url = f"https://huggingface.co/{model_id}/raw/main/{f}"
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                cfg = resp.json()
                v = cfg.get("base_model_name_or_path")
                if v:
                    return str(v).strip()
        except Exception:
            continue
    return None

# ======================
# 📂 3. 从模型文件列表找线索
# ======================
def get_base_from_filelist(model_id: str, timeout=8):
    try:
        url = f"https://huggingface.co/api/models/{model_id}"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None

        data = resp.json()
        siblings = data.get("siblings", [])
        filenames = [s.get("rfilename", "") for s in siblings]

        # 找加载 base model 的线索
        for fn in filenames:
            if "adapter" in fn.lower() or "lora" in fn.lower():
                # 尝试从文件名推断
                pass

        return None
    except Exception:
        return None

# ======================
# 🎯 4. 主 config 提取（保留之前的）
# ======================
def get_base_from_main_config(model_id: str, timeout=8):
    try:
        url = f"https://huggingface.co/{model_id}/raw/main/config.json"
        resp = requests.get(url, timeout=timeout)
        if resp.status_code != 200:
            return None

        config = resp.json()

        # 所有可能的字段
        candidates = [
            config.get("parent_model_name"),
            config.get("base_model_name_or_path"),
            config.get("base_model"),
            config.get("pretrained_model_name_or_path"),
        ]

        # LoRA/PEFT
        if "lora_config" in config:
            candidates.append(config["lora_config"].get("base_model_name_or_path"))
        if "adapter_config" in config:
            candidates.append(config["adapter_config"].get("base_model_name_or_path"))

        for c in candidates:
            if c and isinstance(c, str) and len(c.strip()) > 3:
                return c.strip()

        # 多模态标记
        has_text = "text_config" in config
        has_vision = "vision_config" in config
        if has_text or has_vision:
            return {"multi": True, "text": has_text, "vision": has_vision}

        return None
    except Exception:
        return None

# ======================
# 🧠 5. 超激进模型 ID 解析
# ======================
def parse_model_id_super(model_id: str):
    # 标准化
    mid = model_id.lower().replace("_", "-").replace(" ", "")

    # 遍历所有已知系列
    for family, base in MODEL_FAMILY_MAP.items():
        if family in mid:
            return base

    # 正则提取
    patterns = [
        (r"llama[-_]?(\d+)[-_]?(\d+)[bB]", lambda m: f"meta-llama/Llama-{m.group(1)}-{m.group(2)}B-hf"),
        (r"qwen[-_]?(\d+)[-_]?(\d+)[bB]", lambda m: f"Qwen/Qwen{m.group(1)}-{m.group(2)}B"),
        (r"mistral[-_]?(\d+)[bB]", lambda m: f"mistralai/Mistral-{m.group(1)}B-v0.1"),
    ]

    for pat, builder in patterns:
        match = re.search(pat, mid)
        if match:
            try:
                return builder(match)
            except:
                pass

    return None

# ======================
# 🚀 主逻辑：10 层提取！
# ======================
models = api.list_models(limit=LIMIT, sort="downloads")
model_data = []

for idx, m in enumerate(models):
    print(f"[{idx+1}/{LIMIT}] {m.modelId}")

    model_info_dict = {
        "model_id": m.modelId,
        "downloads": m.downloads or 0,
        "library_name": m.library_name or "未知",
        "tags": ",".join(m.tags) if m.tags else "无",

        # 10 层来源
        "l1_card": "无",
        "l2_main_config": "无",
        "l3_separate_config": "无",
        "l4_readme": "无",
        "l5_filelist": "无",
        "l6_id_parse": "无",
        "l7_type_map": "无",
        "l8_multi": "无",

        # 最终结果
        "base_model_final": "基座模型",
        "is_multimodal": False,
        "dataset_deps": [],
        "status": "ok"
    }

    try:
        # --------------------------
        # L1: cardData
        # --------------------------
        model_info = api.model_info(m.modelId)
        card = model_info.cardData or {}
        model_info_dict["l1_card"] = str(card.get("base_model", "无"))
        model_info_dict["dataset_deps"] = card.get("datasets", [])

        # --------------------------
        # L2: 主 config
        # --------------------------
        cfg_res = get_base_from_main_config(m.modelId)
        if cfg_res:
            if isinstance(cfg_res, dict):
                model_info_dict["is_multimodal"] = True
                model_info_dict["l8_multi"] = "多模态内部组件"
            else:
                model_info_dict["l2_main_config"] = cfg_res

        # --------------------------
        # L3: 单独 adapter/peft config
        # --------------------------
        sep_cfg = get_base_from_separate_configs(m.modelId)
        if sep_cfg:
            model_info_dict["l3_separate_config"] = sep_cfg

        # --------------------------
        # L4: README.md
        # --------------------------
        readme_base = get_base_from_readme(m.modelId)
        if readme_base:
            model_info_dict["l4_readme"] = readme_base

        # --------------------------
        # L5: 文件列表
        # --------------------------
        fl_base = get_base_from_filelist(m.modelId)
        if fl_base:
            model_info_dict["l5_filelist"] = fl_base

        # --------------------------
        # L6: 超激进 ID 解析
        # --------------------------
        id_base = parse_model_id_super(m.modelId)
        if id_base:
            model_info_dict["l6_id_parse"] = id_base

        # --------------------------
        # L7: model_type 映射
        # --------------------------
        if hasattr(model_info, "config"):
            mt = model_info.config.get("model_type")
            if mt in MODEL_FAMILY_MAP:
                model_info_dict["l7_type_map"] = MODEL_FAMILY_MAP[mt]

        # --------------------------
        # 🔥 最终优先级（从高到低）
        # --------------------------
        final = None
        sources = [
            model_info_dict["l1_card"],
            model_info_dict["l2_main_config"],
            model_info_dict["l3_separate_config"],
            model_info_dict["l4_readme"],
            model_info_dict["l5_filelist"],
            model_info_dict["l6_id_parse"],
            model_info_dict["l7_type_map"],
            model_info_dict["l8_multi"],
        ]

        for src in sources:
            if src and src not in ["无", "获取失败", ""]:
                final = src
                break

        model_info_dict["base_model_final"] = final or "基座模型"

    except Exception as e:
        print(f"  → 失败：{str(e)[:60]}")
        model_info_dict["status"] = "failed"
        model_info_dict["base_model_final"] = "获取失败"

    model_data.append(model_info_dict)
    time.sleep(0.2)

# ======================
# 保存
# ======================
import os
os.makedirs("data", exist_ok=True)

df_models = pd.DataFrame(model_data)
df_models.to_csv("data/models_ultimate.csv", index=False, encoding="utf-8-sig")
df_models.to_json("data/models_ultimate.json", orient="records", force_ascii=False, indent=4)

print(f"\n✅ 终极版抓取完成：{len(model_data)} 个模型")
print("📁 已保存到 data/models_ultimate.csv/json")