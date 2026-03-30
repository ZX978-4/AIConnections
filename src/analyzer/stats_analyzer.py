# src/analyzer/stats_analyzer.py
import pandas as pd
import matplotlib.pyplot as plt
import os
from src.config.settings import SAVE_PATHS
from src.utils.common import log

plt.rcParams["font.sans-serif"] = ["SimHei"]
plt.rcParams["axes.unicode_minus"] = False

def run_quantitative_analysis(full_df):
    log("开始供应链定量分析...")
    valid = full_df[full_df["base_model"] != "unknown"]

    # 指标
    ft_ratio = len(valid) / len(full_df) * 100
    top5_base = valid["base_model"].value_counts().head(5)
    top5_data = valid["ft_dataset"].value_counts().head(5)

    # 画图
    fig, (a1, a2, a3) = plt.subplots(1, 3, figsize=(18, 5))
    a1.pie([ft_ratio, 100-ft_ratio], labels=["微调模型", "基础模型"], autopct="%1.1f%%")
    a1.set_title("模型类型占比")

    top5_base.plot.bar(ax=a2, color="green")
    a2.set_title("Top5 基础模型")

    top5_data.plot.bar(ax=a3, color="red")
    a3.set_title("Top5 数据集")

    plt.tight_layout()
    img_path = os.path.join(SAVE_PATHS["images"], "analysis.png")
    plt.savefig(img_path, dpi=300)
    log(f"分析图已保存：{img_path}")