import os
from collections import Counter

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class StatsAnalyzer:
    def __init__(self, nodes_path="data/processed/nodes.csv", edges_path="data/processed/edges.csv"):
        self.nodes_df = pd.read_csv(nodes_path)
        self.edges_df = pd.read_csv(edges_path)
        self.output_dir = "output/images"
        os.makedirs(self.output_dir, exist_ok=True)
        sns.set_style("whitegrid")
        plt.rcParams["font.sans-serif"] = ["SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False

    def analyze_relation_distribution(self):
        """Analyze relation type distribution."""
        relation_counts = self.edges_df["relation"].value_counts()

        fig, ax = plt.subplots(figsize=(12, 6))
        relation_counts.plot(kind="bar", ax=ax, color=sns.color_palette("husl", len(relation_counts)))
        ax.set_title("Relation Type Distribution", fontsize=16, fontweight="bold")
        ax.set_xlabel("Relation Type", fontsize=12)
        ax.set_ylabel("Count", fontsize=12)
        ax.tick_params(axis="x", rotation=45)
        plt.tight_layout()

        output_path = f"{self.output_dir}/relation_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Relation distribution saved: {output_path}")
        return relation_counts

    def analyze_download_distribution(self):
        """Analyze download distribution."""
        models_df = self.nodes_df[self.nodes_df["type"] == "model"]

        fig, axes = plt.subplots(1, 2, figsize=(16, 5))

        top20 = models_df.nlargest(20, "downloads")
        axes[0].barh(range(len(top20)), top20["downloads"], color=sns.color_palette("viridis", len(top20)))
        axes[0].set_yticks(range(len(top20)))
        axes[0].set_yticklabels([name.split("/")[-1] for name in top20["id"]], fontsize=9)
        axes[0].set_xlabel("Downloads", fontsize=12)
        axes[0].set_title("Top 20 Models by Downloads", fontsize=14, fontweight="bold")
        axes[0].invert_yaxis()

        axes[1].hist(models_df["downloads"], bins=50, color="skyblue", edgecolor="black", alpha=0.7)
        axes[1].set_xlabel("Downloads", fontsize=12)
        axes[1].set_ylabel("Models", fontsize=12)
        axes[1].set_title("Download Distribution", fontsize=14, fontweight="bold")
        axes[1].set_xscale("log")

        plt.tight_layout()
        output_path = f"{self.output_dir}/download_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Download distribution saved: {output_path}")

    def analyze_author_contribution(self):
        """Analyze top authors."""
        top_authors = self.nodes_df["author"].value_counts().head(15)

        fig, ax = plt.subplots(figsize=(12, 8))
        ax.barh(range(len(top_authors)), top_authors.values, color=sns.color_palette("Set2", len(top_authors)))
        ax.set_yticks(range(len(top_authors)))
        ax.set_yticklabels(top_authors.index, fontsize=11)
        ax.set_xlabel("Count", fontsize=12)
        ax.set_title("Top 15 Authors", fontsize=16, fontweight="bold")
        ax.invert_yaxis()

        for i, v in enumerate(top_authors.values):
            ax.text(v + 5, i, str(v), va="center", fontsize=10, fontweight="bold")

        plt.tight_layout()
        output_path = f"{self.output_dir}/author_contribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Author contribution saved: {output_path}")
        return top_authors

    def analyze_license_distribution(self):
        """Analyze license distribution."""
        license_counts = self.nodes_df["license"].value_counts().head(10)

        fig, axes = plt.subplots(1, 2, figsize=(16, 6))

        colors = sns.color_palette("husl", len(license_counts))
        axes[0].pie(license_counts.values, labels=license_counts.index, autopct="%1.1f%%", colors=colors, startangle=90)
        axes[0].set_title("License Distribution", fontsize=14, fontweight="bold")

        axes[1].bar(range(len(license_counts)), license_counts.values, color=colors, edgecolor="black", alpha=0.8)
        axes[1].set_xticks(range(len(license_counts)))
        axes[1].set_xticklabels(license_counts.index, rotation=45, ha="right", fontsize=9)
        axes[1].set_ylabel("Count", fontsize=12)
        axes[1].set_title("Top Licenses", fontsize=14, fontweight="bold")

        plt.tight_layout()
        output_path = f"{self.output_dir}/license_distribution.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"License distribution saved: {output_path}")

    def analyze_task_types(self):
        """Analyze task type distribution."""
        models_df = self.nodes_df[self.nodes_df["type"] == "model"]
        task_counts = models_df["task"].value_counts().head(15)

        fig, ax = plt.subplots(figsize=(14, 8))
        colors = sns.color_palette("viridis", len(task_counts))
        bars = ax.barh(range(len(task_counts)), task_counts.values, color=colors, edgecolor="black", alpha=0.8)
        ax.set_yticks(range(len(task_counts)))
        ax.set_yticklabels(task_counts.index, fontsize=11)
        ax.set_xlabel("Models", fontsize=12)
        ax.set_title("Top 15 Task Types", fontsize=16, fontweight="bold")
        ax.invert_yaxis()

        for i, (bar, v) in enumerate(zip(bars, task_counts.values)):
            ax.text(v + 20, i, str(v), va="center", fontsize=10, fontweight="bold")

        plt.tight_layout()
        output_path = f"{self.output_dir}/task_types.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()
        print(f"Task types saved: {output_path}")
        return task_counts

    def analyze_network_stats(self):
        """Analyze basic network stats."""
        models_df = self.nodes_df[self.nodes_df["type"] == "model"]
        datasets_df = self.nodes_df[self.nodes_df["type"] == "dataset"]

        in_degree = self.edges_df["target"].value_counts()
        out_degree = self.edges_df["source"].value_counts()

        stats = {
            "total_models": len(models_df),
            "total_datasets": len(datasets_df),
            "total_relations": len(self.edges_df),
            "avg_degree": len(self.edges_df) / len(self.nodes_df),
            "max_in_degree": in_degree.max() if len(in_degree) > 0 else 0,
            "max_out_degree": out_degree.max() if len(out_degree) > 0 else 0,
        }

        return stats

    def generate_all_charts(self):
        """Generate all analysis charts."""
        print("Generating charts...")
        self.analyze_relation_distribution()
        self.analyze_download_distribution()
        self.analyze_author_contribution()
        self.analyze_license_distribution()
        self.analyze_task_types()
        stats = self.analyze_network_stats()

        print("\nNetwork stats:")
        for key, value in stats.items():
            print(f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}")

        print(f"\nAll charts saved to: {self.output_dir}")
        return stats


if __name__ == "__main__":
    analyzer = StatsAnalyzer()
    analyzer.generate_all_charts()
