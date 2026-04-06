import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from collections import Counter

class StatsAnalyzer:
    def __init__(self, nodes_path="data/processed/nodes.csv", edges_path="data/processed/edges.csv"):
        self.nodes_df = pd.read_csv(nodes_path)
        self.edges_df = pd.read_csv(edges_path)
        self.output_dir = "output/images"
        os.makedirs(self.output_dir, exist_ok=True)
        sns.set_style("whitegrid")
        plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

    def analyze_relation_distribution(self):
        """分析关系类型分布"""
        relation_counts = self.edges_df['relation'].value_counts()
        
        fig, ax = plt.subplots(figsize=(12, 6))
        relation_counts.plot(kind='bar', ax=ax, color=sns.color_palette("husl", len(relation_counts)))
        ax.set_title("供应链关系类型分布", fontsize=16, fontweight='bold')
        ax.set_xlabel("关系类型", fontsize=12)
        ax.set_ylabel("数量", fontsize=12)
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        
        output_path = f"{self.output_dir}/relation_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 关系分布图已保存: {output_path}")
        return relation_counts

    def analyze_download_distribution(self):
        """分析下载量分布"""
        models_df = self.nodes_df[self.nodes_df['type'] == 'model']
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 5))
        
        # 柱状图 - 按下载量排序前20
        top20 = models_df.nlargest(20, 'downloads')
        axes[0].barh(range(len(top20)), top20['downloads'], color=sns.color_palette("viridis", len(top20)))
        axes[0].set_yticks(range(len(top20)))
        axes[0].set_yticklabels([name.split('/')[-1] for name in top20['id']], fontsize=9)
        axes[0].set_xlabel("下载量", fontsize=12)
        axes[0].set_title("下载量Top20模型", fontsize=14, fontweight='bold')
        axes[0].invert_yaxis()
        
        # 直方图 - 下载量分布
        axes[1].hist(models_df['downloads'], bins=50, color='skyblue', edgecolor='black', alpha=0.7)
        axes[1].set_xlabel("下载量", fontsize=12)
        axes[1].set_ylabel("模型数", fontsize=12)
        axes[1].set_title("下载量分布直方图", fontsize=14, fontweight='bold')
        axes[1].set_xscale('log')
        
        plt.tight_layout()
        output_path = f"{self.output_dir}/download_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 下载量分析图已保存: {output_path}")

    def analyze_author_contribution(self):
        """分析顶级作者的贡献"""
        top_authors = self.nodes_df['author'].value_counts().head(15)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.barh(range(len(top_authors)), top_authors.values, color=sns.color_palette("Set2", len(top_authors)))
        ax.set_yticks(range(len(top_authors)))
        ax.set_yticklabels(top_authors.index, fontsize=11)
        ax.set_xlabel("贡献数量", fontsize=12)
        ax.set_title("模型/数据集作者Top15", fontsize=16, fontweight='bold')
        ax.invert_yaxis()
        
        # 添加数值标签
        for i, v in enumerate(top_authors.values):
            ax.text(v + 5, i, str(v), va='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        output_path = f"{self.output_dir}/author_contribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 作者贡献分析图已保存: {output_path}")
        return top_authors

    def analyze_license_distribution(self):
        """分析许可证分布"""
        license_counts = self.nodes_df['license'].value_counts().head(10)
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 饼图
        colors = sns.color_palette("husl", len(license_counts))
        axes[0].pie(license_counts.values, labels=license_counts.index, autopct='%1.1f%%', 
                   colors=colors, startangle=90)
        axes[0].set_title("许可证分布", fontsize=14, fontweight='bold')
        
        # 柱状图
        axes[1].bar(range(len(license_counts)), license_counts.values, color=colors, edgecolor='black', alpha=0.8)
        axes[1].set_xticks(range(len(license_counts)))
        axes[1].set_xticklabels(license_counts.index, rotation=45, ha='right', fontsize=9)
        axes[1].set_ylabel("数量", fontsize=12)
        axes[1].set_title("许可证分布详情", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        output_path = f"{self.output_dir}/license_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 许可证分析图已保存: {output_path}")

    def analyze_task_types(self):
        """分析任务类型分布"""
        models_df = self.nodes_df[self.nodes_df['type'] == 'model']
        task_counts = models_df['task'].value_counts().head(15)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        colors = sns.color_palette("viridis", len(task_counts))
        bars = ax.barh(range(len(task_counts)), task_counts.values, color=colors, edgecolor='black', alpha=0.8)
        ax.set_yticks(range(len(task_counts)))
        ax.set_yticklabels(task_counts.index, fontsize=11)
        ax.set_xlabel("模型数", fontsize=12)
        ax.set_title("模型任务类型Top15分布", fontsize=16, fontweight='bold')
        ax.invert_yaxis()
        
        # 添加数值标签
        for i, (bar, v) in enumerate(zip(bars, task_counts.values)):
            ax.text(v + 20, i, str(v), va='center', fontsize=10, fontweight='bold')
        
        plt.tight_layout()
        output_path = f"{self.output_dir}/task_types.png"
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"✅ 任务类型分析图已保存: {output_path}")
        return task_counts

    def analyze_network_stats(self):
        """分析网络统计信息"""
        models_df = self.nodes_df[self.nodes_df['type'] == 'model']
        datasets_df = self.nodes_df[self.nodes_df['type'] == 'dataset']
        
        # 计算入度和出度
        in_degree = self.edges_df['target'].value_counts()
        out_degree = self.edges_df['source'].value_counts()
        
        stats = {
            "总模型数": len(models_df),
            "总数据集数": len(datasets_df),
            "总关系数": len(self.edges_df),
            "平均入度": len(self.edges_df) / len(self.nodes_df),
            "最大入度": in_degree.max() if len(in_degree) > 0 else 0,
            "最大出度": out_degree.max() if len(out_degree) > 0 else 0,
        }
        
        return stats

    def generate_all_charts(self):
        """生成所有分析图表"""
        print("开始生成可视化分析图表...")
        self.analyze_relation_distribution()
        self.analyze_download_distribution()
        self.analyze_author_contribution()
        self.analyze_license_distribution()
        self.analyze_task_types()
        stats = self.analyze_network_stats()
        
        print("\n📊 网络统计信息:")
        for key, value in stats.items():
            print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")
        
        print(f"\n✅ 所有图表已保存到: {self.output_dir}")
        return stats

if __name__ == "__main__":
    analyzer = StatsAnalyzer()
    analyzer.generate_all_charts()
