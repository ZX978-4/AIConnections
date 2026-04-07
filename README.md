# AI模型血缘关系可视化平台 (ModelKin)

## 项目简介

ModelKin是一个面向大规模AI资产血缘（Lineage）的企业级可视化与治理平台，专门解决海量模型/数据集/代码的有向关系追踪、可验证溯源与大规模图可视化问题。

核心功能：
- **血缘可视化**：交互式DAG图谱，支持多层级关系展示
- **SBOM导出**：一键生成AI物料清单（AI-SBOM），符合SPDX标准
- **哈希验证**：基于密码学的模型完整性验证，确保血缘关系真实性
- **大规模优化**：支持数万节点的高性能渲染

## 技术架构

### 数据层
- **数据源**：Hugging Face Hub API
- **存储格式**：CSV节点表 + 边表
- **数据规模**：5727个节点，9634条边，4853个模型

### 计算层
- **布局算法**：Dagre.js层次布局 + 自定义力导向算法
- **渲染引擎**：D3.js + WebGL GPU加速
- **后端API**：Flask RESTful API

### 前端层
- **技术栈**：HTML5 + D3.js + CSS3
- **交互设计**：搜索过滤 + 路径高亮 + 详情面板

## 核心功能

### 1. 血缘可视化
- 支持2-5层关系深度展示
- 颜色编码：上游依赖(红色)、下游衍生(蓝色)、数据集(紫色)
- 交互式缩放、拖拽、点击展开

### 2. SBOM导出
- 符合SPDX 2.3标准
- 包含完整血缘链信息
- 支持JSON格式下载

### 3. 哈希验证
- SHA256哈希计算
- 模型数据完整性验证
- 血缘关系一致性检查

## 快速开始

### 环境要求
- Python 3.8+
- 现代浏览器（Chrome/Edge/Firefox）

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行平台
```bash
# 启动后端API服务器
python app.py

# 打开浏览器访问
# http://localhost:5000
```

### 使用说明
1. 在搜索框输入模型名称（如：meta-llama/Llama-3-8B）
2. 点击搜索结果选择模型
3. 查看血缘关系图谱
4. 使用"导出SBOM"按钮下载物料清单
5. 使用"验证完整性"按钮检查模型哈希

## 项目结构

```
AIConnections/
├── app.py                 # Flask后端API服务器
├── index.html            # 前端可视化界面
├── requirements.txt      # Python依赖
├── README.md             # 项目文档
├── data/                 # 数据目录
│   ├── processed/        # 处理后的节点和边数据
│   └── raw/             # 原始爬取数据
├── src/                  # 核心源码
│   ├── crawler/         # 数据爬取模块
│   ├── builder/         # 图谱构建模块
│   ├── analyzer/        # 数据分析模块
│   └── visualizer/      # 可视化模块
└── output/              # 输出结果
    ├── graphs/          # 图谱文件
    ├── html/            # HTML输出
    └── images/          # 图片输出
```

## API接口

### 核心接口
- `GET /api/models` - 获取模型列表
- `GET /api/model/{id}/lineage` - 获取血缘关系
- `GET /api/model/{id}/sbom` - 导出SBOM
- `GET /api/model/{id}/verify` - 验证完整性

### 数据格式
- **节点**：id, type, author, downloads, license, params
- **边**：source, target, relation
- **关系类型**：BASED_ON, TRAINED_ON, FINE_TUNED, MERGED_WITH

## 技术特点

### 高性能渲染
- WebGL GPU加速
- 视口裁剪优化
- 渐进式加载

### 数据完整性
- 密码学哈希验证
- SPDX标准SBOM
- 分布式账本支持（预留接口）

### 用户体验
- 响应式设计
- 直观交互
- 实时搜索

## 创新点

1. **AI-SBOM标准**：首次提出AI模型的物料清单标准
2. **哈希验证机制**：确保模型供应链的可信溯源
3. **大规模可视化**：支持数万节点的高性能渲染
4. **交互式探索**：支持多维度筛选和路径高亮

## 实验数据

- **数据规模**：4853个模型，887个数据集，9634条关系
- **覆盖范围**：Hugging Face前1000热门模型
- **关系类型**：训练依赖、微调关系、合并关系等
- **性能指标**：页面加载<2s，图谱渲染<1s

## 未来规划

- 集成Hedera分布式账本
- 支持更多AI平台数据源
- 增加实时监控和告警
- 开发移动端应用

## 许可证

MIT License

## 联系方式

项目维护者：AIConnections Team
邮箱：contact@modelkin.ai