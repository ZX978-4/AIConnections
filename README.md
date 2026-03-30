 # note
 
 除了传统的程序代码开源，开源也影响到了其他领域，
 例如：人工智能。与通常的软件开源不同，人工智能开源涉及到数据集、训练算法、
 调优工具和AI模型等。Hugging Face是当前最知名的AI模型和数据集汇聚平台，平台聚
 集了200多万模型和50多万个数据集。此外，GitHub、ModelScope等平台上也有大量的数据
 和模型资源。一个模型是基于一个或者多个数据集上训练而来，所以模型依赖于相关的数据集。对于预
 训练模型而言，基于特定的数据集可以对其进行精调，从而得到新的模型。这样模型之间以及模型与
 数据集之间就形成了依赖关系，即人工智能模型的供应链。	本题目要求从网络平台上爬取数据
 集及模型相关数据，实现AI模型供应链的构建，并对其特点进行定量和定性分析。提供浏览AI模型供应链的可视化
 界面。
### 参考资料：https://github.com/Data-Provenance-Initiative/Data-Provenance-Collection 
    https://github.com/stanford-crfm/ecosystem-graphs 







hf_ai_supply_chain/          # 项目根目录（PyCharm 项目文件夹）
├── .env                     # 环境变量（HF Token，私密配置）
├── .gitignore               # Git忽略文件（排除虚拟环境、数据、缓存）
├── requirements.txt         # 项目依赖清单
├── README.md                # 项目说明（使用方法、产出物）
├── main.py                  # 🚀 主入口脚本（一键执行全流程）
├── streamlit_app.py         # 🌐 Web可视化界面入口
│
├── src/                     # 🔧 核心源码包（PyCharm标记为 Sources Root）
│   ├── __init__.py          # 标记为Python包
│   │
│   ├── config/              # 配置模块：全局常量、认证、参数
│   │   ├── __init__.py
│   │   └── settings.py      # HF API配置、爬取参数、正则规则
│   │
│   ├── crawler/             # 爬取模块：HF模型/数据集获取
│   │   ├── __init__.py
│   │   └── hf_api.py        # 调用HF官方API，获取Top1000热门模型
│   │
│   ├── parser/              # 解析模块：Model Card依赖提取
│   │   ├── __init__.py
│   │   └── model_parser.py  # 正则/LLM解析基础模型、数据集依赖
│   │
│   ├── builder/             # 供应链构建模块：节点/边/图谱生成
│   │   ├── __init__.py
│   │   └── graph_builder.py # 生成标准化节点表、边表、NetworkX图谱
│   │
│   ├── analyzer/            # 分析模块：定量+定性分析、图表生成
│   │   ├── __init__.py
│   │   └── stats_analyzer.py # 统计指标、可视化图表、特征分析
│   │
│   ├── visualizer/          # 可视化模块：交互式图谱生成
│   │   ├── __init__.py
│   │   └── pyvis_builder.py # 生成PyVis交互式HTML图谱
│   │
│   └── utils/               # 工具模块：通用函数（日志、异常、清洗）
│       ├── __init__.py
│       └── common.py        # 延时、数据去重、文件保存、日志工具
│
├── data/                    # 📊 数据目录：原始数据+结构化数据
│   ├── raw/                 # 原始爬取数据（模型基础信息）
│   └── processed/           # 处理后数据（节点表、边表、完整模型表）
│
└─── output/                  # 📤 输出目录：所有最终产物
    ├── graphs/              # 图谱文件（GEXF格式）
    ├── images/              # 分析图表（PNG格式）
    └── html/                # 交互式可视化页面（HTML格式）



