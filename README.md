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





理解了，我会用更准确、直白的专业语言来描述。这份 `README.md` 重点突出了你的**爬取逻辑**、**深度控制**以及**稳定性保障**机制。

---

# AI 模型供应链数据采集工具 (HF-ASCE)

本程序专门用于从 Hugging Face 平台自动化采集模型与数据集的依赖数据，旨在构建 AI 模型的供应链拓扑结构。

## 1. 核心爬取策略

为了平衡数据覆盖面与采集效率，程序采用了以下逻辑：

* **种子节点筛选**：初始运行阶段，程序会通过 API 获取下载量排名前 1000 的热门模型作为种子节点。
* **多维关系解析**：
    * **上游溯源**：解析模型元数据中的 `base_model` 字段，识别其父级模型。
    * **下游探索**：通过搜索 API 查找引用了当前模型的衍生版本（包括微调、量化、合并和蒸馏版本）。
    * **依赖识别**：提取模型关联的数据集信息。
* **动态深度控制**：程序会根据模型的下载量（影响力）动态调整递归深度。对于高热度模型，会进一步挖掘其下游生态；对于低热度模型，则限制搜索范围以节省资源。

## 2. 系统稳定性与连接保障

针对大规模网络请求中常见的连接中断和速率限制问题，程序实现了以下机制：

* **容错与重试 (Retry with Backoff)**：
    * 封装了 `_safe_get` 请求函数，当遇到网络抖动或 HTTP 429 (Too Many Requests) 时，程序会触发**指数退避算法**进行重试，逐步增加等待时间。
* **断点续传 (Checkpointing)**：
    * **实时快照**：每处理 50 个模型，程序会自动将内存中的已访问列表和已采集数据存入 `supply_chain_checkpoint.json`。
    * **状态恢复**：程序启动时会检测是否存在快照文件。若存在，将自动加载数据并过滤掉已处理的模型，从中断处继续运行。
* **会话管理**：
    * 使用 `requests.Session` 复用 TCP 连接，并配置了标准的 `User-Agent`，以减少频繁建立连接带来的开销。

## 3. 使用方法

1.  **安装依赖**：`pip install -r requirements.txt`。
2.  **配置环境**：在 `.env` 文件中设置 `HF_TOKEN`。
3.  **运行程序**：执行 `python main.py`。

## 4. 输出数据说明

* **原始数据**：`data/raw/full_supply_chain_data.json`（完整的结构化 JSON）。
* **处理后数据**：
    * `nodes.csv`：包含模型/数据集的 ID、作者、下载量、许可证等属性。
    * `edges.csv`：包含源节点、目标节点及具体的关系类型（如 `fine-tune`, `quantization`, `trained_on` 等）。



