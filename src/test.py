# -*- coding: utf-8 -*-
from pyecharts import options as opts
from pyecharts.charts import Graph

# 1. 准备数据
nodes = [
    {"name": "中心节点", "symbolSize": 50, "category": 0},
    {"name": "节点A", "symbolSize": 30, "category": 1},
    {"name": "节点B", "symbolSize": 30, "category": 1},
    {"name": "子节点1", "symbolSize": 20, "category": 2},
]

links = [
    {"source": "中心节点", "target": "节点A"},
    {"source": "中心节点", "target": "节点B"},
    {"source": "节点A", "target": "子节点1"},
]

categories = [{"name": "核心"}, {"name": "层级一"}, {"name": "层级二"}]


# 2. 绘图配置
def create_graph():
    c = (
        Graph(init_opts=opts.InitOpts(width="1000px", height="600px"))
        .add(
            series_name="关系图",
            nodes=nodes,
            links=links,
            categories=categories,
            layout="force",  # 必填：力导向布局
            is_roam=True,  # 缩放平移
            is_draggable=True,  # 节点拖拽
            is_focusnode=True,  # 焦点高亮
            label_opts=opts.LabelOpts(is_show=True),

            # --- 兼容性修改：如果上述报错，尝试直接传参或留空 ---
            # 绝大多数版本支持直接在 add 里通过这些参数控制：
            repulsion=4000,  # 斥力
            edge_length=100,  # 线长
            gravity=0.2  # 引力
            # ----------------------------------------------
        )
        .set_global_opts(
            title_opts=opts.TitleOpts(title="力导向交互图"),
            legend_opts=opts.LegendOpts(pos_left="2%", pos_top="15%", orient="vertical")
        )
    )
    return c


if __name__ == "__main__":
    try:
        chart = create_graph()
        chart.render("force_result.html")
        print("成功生成 force_result.html！请在浏览器查看。")
    except Exception as e:
        print(f"仍然报错: {e}")
        print("提示：如果还是报错，请尝试把 .add() 里的 repulsion 和 edge_length 删掉运行。")