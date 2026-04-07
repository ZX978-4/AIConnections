from typing import List, Dict, Tuple


def get_sample_nodes_edges() -> Tuple[List[Dict], List[Dict]]:
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
        {"id": "chavinlo/alpaca-native", "type": "model", "author": "chavinlo", "downloads": 500000, "license": "CC BY-NC 4.0", "params": "7B"},
    ]

    edges_data = [
        {"source": "meta-llama/Llama-3-8B", "target": "HuggingFaceH4/zephyr-7b-beta", "relation": "BASED_ON"},
        {"source": "meta-llama/Llama-3-8B", "target": "lmsys/vicuna-7b-v1.5", "relation": "BASED_ON"},
        {"source": "EleutherAI/the-pile", "target": "meta-llama/Llama-3-8B", "relation": "TRAINED_ON"},
        {"source": "EleutherAI/the-pile", "target": "meta-llama/Llama-3-70B", "relation": "TRAINED_ON"},
        {"source": "mistralai/Mistral-7B-v0.1", "target": "mistralai/Mistral-7B-Instruct", "relation": "FINE_TUNED"},
        {"source": "meta-llama/Llama-3-8B", "target": "HuggingFaceH4/zephyr-7b-alpha", "relation": "BASED_ON"},
        {"source": "EleutherAI/the-pile", "target": "openlm-research/open_llama_7b", "relation": "TRAINED_ON"},
        {"source": "openlm-research/open_llama_7b", "target": "chavinlo/alpaca-native", "relation": "FINE_TUNED"},
        {"source": "chavinlo/alpaca-native", "target": "lmsys/vicuna-7b-v1.5", "relation": "MERGED_WITH"},
    ]

    return nodes_data, edges_data
