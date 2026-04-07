# AI Model Lineage Visualization Platform (ModelKin)

一个用于展示大模型与数据集之间“血缘关系”的可视化与查询平台，支持 REST API 查询、SBOM 导出与完整性验证。

## 功能概览
- 交互式血缘图查询（父/子/完整血缘）
- SBOM（SPDX 2.3）导出
- 基于哈希的完整性验证
- 统计分析与图表输出（可选）

## 快速开始

### 1) 安装依赖
```bash
pip install -r requirements.txt
```

### 2) 启动后端 API
```bash
python app.py
```
浏览器访问：`http://localhost:5000`

### 3) 运行演示脚本（可选）
```bash
python demo.py
```

## 数据与爬虫

如果 `data/processed/nodes.csv` 或 `edges.csv` 不存在，系统会自动生成一份示例数据。

如需抓取 Hugging Face 数据并生成真实数据：
```bash
python crawler.py
```

可在 `.env` 中配置：
```
HF_TOKEN=your_hf_token
```

## 统计分析（可选）
```bash
python -m src.analyzer.stats_analyzer
```
图表输出到 `output/images`。

## API 说明
- `GET /api/health` 获取服务状态
- `GET /api/models?q=xxx` 模型搜索
- `GET /api/nodes` 获取节点
- `GET /api/edges` 获取边
- `GET /api/model/{id}` 获取模型详情
- `GET /api/model/{id}/parents` 父级依赖
- `GET /api/model/{id}/children` 子级派生
- `GET /api/model/{id}/lineage?depth=2` 获取血缘（支持深度）
- `GET /api/model/{id}/sbom?depth=5` 导出 SBOM
- `GET /api/model/{id}/verify` 完整性验证

## 数据格式

**nodes.csv**
```
id,type,author,downloads,license,task,params
```

**edges.csv**
```
source,target,relation
```

## 项目结构
```
AIConnections/
├─ app.py                   # Flask API
├─ index.html               # 前端页面
├─ demo.py                  # API 演示脚本
├─ crawler.py               # 数据爬虫入口
├─ requirements.txt
├─ data/
│  ├─ raw/                  # 原始数据
│  └─ processed/            # 处理后的 nodes/edges
├─ src/
│  ├─ crawler/              # Hugging Face 爬虫
│  ├─ builder/              # 图谱构建
│  ├─ parser/               # 关系解析
│  ├─ analyzer/             # 统计分析
│  ├─ utils/                # 工具与样例数据
│  └─ config/               # 配置
└─ viewer/                  # 可视化工具（Streamlit 依赖）
```

## 备注
- `viewer/` 目录包含一些 Streamlit 工具函数，非 API 必需。
- 如果要减小依赖，可自行将 `streamlit` 从 `requirements.txt` 移除。

## License
MIT
