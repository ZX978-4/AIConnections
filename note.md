## AI Lineage Explorer
AI Lineage Explorer（由 EQTY Lab 开发） 是面向大规模 AI 资产血缘（Lineage） 的企业级可视化与治理平台，核心解决海量模型 / 数据 / 代码的有向关系追踪、可验证溯源与大规模图可视化问题，非常贴合你做 Hugging Face 大模型 base_model 关系图谱的需求。
## 解决的问题
• Create safer, smarter AI. Bind policies to agents and models at runtime. 

• Achieve continuous, end-to-end compliance and assurance at the code level.

• Secure your entire AI supply chain with persistent, auditable proofs.


决你的核心难点（大规模有向图）
节点太多（10 万 +）：分层聚合 + 渐进式加载，内存可控
边太密（交叉严重）：边捆绑 + Dagre 层次布局，方向清晰
交互卡顿：WebGL GPU 渲染，帧率稳定
找不到目标：搜索 + 过滤 + 路径高亮，快速定位



技术架构（可直接复用）
1. 数据层（存储大规模有向图）
图数据库：Neo4j（单机）/ JanusGraph + Cassandra（分布式）
支持1 亿 + 节点、5 亿 + 边，适合你的 Hugging Face 全量模型
原生支持 Cypher 查询，快速检索 “所有基于 X 的模型”
元数据存储：PostgreSQL（结构化）+ Elasticsearch（搜索）
数据采集：
对接 Hugging Face Hub API，自动爬取base_model、model_id、author、downloads
支持增量更新，避免全量重爬
2. 计算层（布局 + 渲染加速）
布局引擎：
Dagre.js（DAG 层次布局）
自定义力导向算法（O (n log n) 复杂度）
GNN 预计算节点坐标（替代迭代，提速 10–100 倍）
渲染引擎：
WebGL + Three.js（GPU 加速）
边捆绑算法（减少视觉混乱）
视口动态裁剪（内存优化）
3. 前端层（交互体验）
技术栈：React + D3.js + WebSocket
核心组件：
Graph Explorer：交互式有向图画布
Filter Panel：多维度筛选（模型家族、参数、作者）
Detail Panel：节点详情抽屉
Search Bar：全文检索 + 路径查询
Export：导出 SBOM / 图片 / GraphML


AI Integrity Suite 是一套基于密码学、分布式账本（Hedera 网络）和图可视化技术的企业级 AI 治理平台，核心解决 AI 系统的可信溯源、合规审计、大规模血缘可视化三大痛点，完美匹配你做 Hugging Face 大模型 base_model 关系图谱的需求。


核心定位：全球首款 AI 全链路血缘可视化与审计工具，专门解决大规模有向图可视化的核心痛点
核心功能（完全匹配你的大模型血缘项目）：
全链路 AI 资产建模：支持模型（含 base_model 派生关系）、数据集、代码、Agent、算力等多类型节点，精准对应child_model → base_model的有向血缘关系
大规模有向图可视化优化：
分层聚合（Super Node）：按模型家族、作者、参数规模自动聚类，先看全局概览，再展开细节
渐进式加载 + 视口裁剪：仅渲染当前屏幕可见区域，支持百万级节点 / 边的流畅交互
DAG 专用层次布局：针对模型派生这类无环有向关系，用 Dagre.js 优化布局，彻底解决边交叉、方向混乱问题
WebGL GPU 加速渲染：替代传统 Canvas，保证 30fps 以上的拖拽、缩放、高亮交互
可信溯源与审计：
基于密码学和 Hedera 分布式账本，为每一条血缘关系生成不可篡改的哈希凭证，验证模型是否真的基于某 base_model，防伪造
一键生成 AI SBOM（AI 物料清单），包含完整血缘链，可导出用于合规审计
交互设计：严格遵循「概览→缩放→过滤→详情→查询」的信息检索范式，解决视觉过载
极简部署：支持一行代码接入，自动采集 Hugging Face 等平台的模型元数据
适用场景：大模型家族血缘可视化、AI 开发全链路溯源、企业 AI 资产审计