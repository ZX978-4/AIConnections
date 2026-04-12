// API配置
const API_BASE = 'http://localhost:5000/api';

// 状态
let state = {
    currentModel: null,
    depth: 2,
    lineageData: null,
    searchTimeout: null
};

// 初始化SVG
const width = window.innerWidth - 320;
const height = window.innerHeight;

const svg = d3.select("#graph")
    .append("svg")
    .attr("width", width)
    .attr("height", height);

// 箭头
svg.append("defs").append("marker")
    .attr("id", "arrow")
    .attr("viewBox", "0 -5 10 10")
    .attr("refX", 20)
    .attr("refY", 0)
    .attr("markerWidth", 6)
    .attr("markerHeight", 6)
    .attr("orient", "auto")
    .append("path")
    .attr("d", "M0,-5L10,0L0,5")
    .attr("class", "arrow");

const g = svg.append("g");

const zoom = d3.zoom()
    .scaleExtent([0.1, 4])
    .on("zoom", (e) => g.attr("transform", e.transform));

svg.call(zoom);

const loadingDiv = d3.select("#graph").select(".loading");
const tooltipEl = document.getElementById('tooltip');

// API调用
async function fetchAPI(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showError(`API连接失败: ${error.message}<br>请确保后端服务已启动: python app.py`);
        return null;
    }
}

function showError(msg) {
    d3.select("#graph").html(`<div class="error">${msg}</div>`);
}

// 搜索功能
document.getElementById('searchInput').addEventListener('input', (e) => {
    clearTimeout(state.searchTimeout);
    const query = e.target.value.trim();

    if (!query) {
        document.getElementById('searchResults').style.display = 'none';
        return;
    }

    state.searchTimeout = setTimeout(async () => {
        const models = await fetchAPI(`/models?q=${encodeURIComponent(query)}`);
        if (models) {
            renderSearchResults(models);
        }
    }, 300);
});

function renderSearchResults(models) {
    const container = document.getElementById('searchResults');
    if (models.length === 0) {
        container.innerHTML = '<div class="search-item">未找到匹配模型</div>';
    } else {
        container.innerHTML = models.map(m => `
          <div class="search-item" data-model="${m}">
            <div>${m.split('/').pop()}</div>
            <small>${m}</small>
          </div>
        `).join('');

        container.querySelectorAll('.search-item').forEach(item => {
            item.addEventListener('click', () => {
                selectModel(item.dataset.model);
                container.style.display = 'none';
                document.getElementById('searchInput').value = '';
            });
        });
    }
    container.style.display = 'block';
}

// 选择模型
async function selectModel(modelId) {
    state.currentModel = modelId;
    const depth = parseInt(document.getElementById('depthSelect').value);

    // 加载血缘数据
    const data = await fetchAPI(`/model/${encodeURIComponent(modelId)}/lineage?depth=${depth}`);
    if (!data) return;

    state.lineageData = data;

    // 更新UI
    updateSidebar(data);
    updateInfoBar(data.model);
    renderGraph(data);
}

function updateSidebar(data) {
    // 当前模型
    document.getElementById('currentModelSection').style.display = 'block';
    document.getElementById('currentModelName').textContent = data.model.id.split('/').pop();
    document.getElementById('currentModelMeta').textContent = `${data.model.author} · ${data.model.params} · ${formatDownloads(data.model.downloads)}`;

    // 统计
    document.getElementById('statAncestors').textContent = data.stats.ancestors_count;
    document.getElementById('statDescendants').textContent = data.stats.descendants_count;
    document.getElementById('statTotal').textContent = data.stats.total_related;
    document.getElementById('statDepth').textContent = data.stats.depth || document.getElementById('depthSelect').value;

    // 上游面板
    const parentsPanel = document.getElementById('parentsPanel');
    if (data.ancestors.length === 0) {
        parentsPanel.innerHTML = '<div style="color: #666; font-size: 12px; text-align: center; padding: 20px;">无上游依赖</div>';
    } else {
        parentsPanel.innerHTML = data.ancestors.map(a => `
          <div class="relation-card" data-model="${a.id}">
            <div class="title">${a.id.split('/').pop()}</div>
            <div class="meta">${a.info.author} · ${formatDownloads(a.info.downloads)}</div>
            <span class="badge">${a.relation} · 深度${a.depth}</span>
          </div>
        `).join('');
    }

    // 下游面板
    const childrenPanel = document.getElementById('childrenPanel');
    if (data.descendants.length === 0) {
        childrenPanel.innerHTML = '<div style="color: #666; font-size: 12px; text-align: center; padding: 20px;">无下游衍生</div>';
    } else {
        childrenPanel.innerHTML = data.descendants.map(d => `
          <div class="relation-card" data-model="${d.id}">
            <div class="title">${d.id.split('/').pop()}</div>
            <div class="meta">${d.info.author} · ${formatDownloads(d.info.downloads)}</div>
            <span class="badge">${d.relation} · 深度${d.depth}</span>
          </div>
        `).join('');
    }

    // 绑定卡片点击
    document.querySelectorAll('.relation-card').forEach(card => {
        card.addEventListener('click', () => {
            selectModel(card.dataset.model);
        });
    });
}

function updateInfoBar(model) {
    document.getElementById('infoBar').style.display = 'flex';
    document.getElementById('infoName').textContent = model.id.split('/').pop();
    document.getElementById('infoAuthor').textContent = model.author;
    document.getElementById('infoDownloads').textContent = formatDownloads(model.downloads);
}

function formatDownloads(num) {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(0) + 'K';
    return num.toString();
}

// 修改后的 renderGraph 函数 - 严格使用后端返回的 parent_id

function renderGraph(data) {
    if (!loadingDiv.empty()) {
        loadingDiv.style('display', 'none');
    }

    // 构建节点映射
    const nodeMap = new Map();
    const centerId = data.model.id;

    // 中心节点
    nodeMap.set(centerId, {
        ...data.model,
        id: centerId,
        isCenter: true,
        depth: 0
    });

    // 添加祖先节点（上游）- 深度为负
    data.ancestors.forEach(a => {
        if (!nodeMap.has(a.id)) {
            nodeMap.set(a.id, {
                ...a.info,
                id: a.id,
                isCenter: false,
                depth: -a.depth,
                relation: a.relation,
                // 严格使用后端返回的 parent_id
                parentId: a.parent_id
            });
        }
    });

    // 添加后代节点（下游）- 深度为正
    data.descendants.forEach(d => {
        if (!nodeMap.has(d.id)) {
            nodeMap.set(d.id, {
                ...d.info,
                id: d.id,
                isCenter: false,
                depth: d.depth,
                relation: d.relation,
                // 严格使用后端返回的 parent_id
                parentId: d.parent_id
            });
        }
    });

    const allNodes = Array.from(nodeMap.values());

    // 构建边 - 严格根据 parentId 连接
    const links = [];
    allNodes.forEach(node => {
        // 只为中心节点以外的节点创建边，且 parentId 必须存在且在 nodeMap 中
        if (!node.isCenter && node.parentId && nodeMap.has(node.parentId)) {
            links.push({
                source: node.parentId,
                target: node.id,
                relation: node.relation
            });
        }
    });

    // 调试输出 - 检查连接关系
    console.log("Links:", links.map(l => `${l.source} -> ${l.target}`));
    console.log("Ancestors parent_id:", data.ancestors.map(a => `${a.id}(depth=${a.depth}): parent=${a.parent_id}`));
    console.log("Descendants parent_id:", data.descendants.map(d => `${d.id}(depth=${d.depth}): parent=${d.parent_id}`));

    // 清除旧内容
    g.selectAll("*").remove();

    // 树状布局计算
    const levelWidth = 220;
    const nodeHeight = 80;

    // 按深度分组
    const nodesByDepth = new Map();
    allNodes.forEach(node => {
        const d = node.depth;
        if (!nodesByDepth.has(d)) nodesByDepth.set(d, []);
        nodesByDepth.get(d).push(node);
    });

    // 计算位置 - 确保同层节点不重叠
    const centerX = width / 2;
    const centerY = height / 2;
    const depthKeys = Array.from(nodesByDepth.keys()).sort((a, b) => a - b);

    depthKeys.forEach(depth => {
        const nodesAtDepth = nodesByDepth.get(depth);
        const x = centerX + depth * levelWidth;
        const totalHeight = (nodesAtDepth.length - 1) * nodeHeight;
        const startY = centerY - totalHeight / 2;

        nodesAtDepth.forEach((node, i) => {
            node.x = x;
            node.y = startY + i * nodeHeight;
        });
    });

    // 绘制连线 - 使用贝塞尔曲线
    const link = g.selectAll(".link")
        .data(links)
        .enter()
        .append("path")
        .attr("class", "link")
        .attr("d", d => {
            const source = nodeMap.get(d.source);
            const target = nodeMap.get(d.target);
            if (!source || !target) return "";

            // 水平贝塞尔曲线
            const dx = target.x - source.x;
            return `M${source.x},${source.y} 
                    C${source.x + dx * 0.5},${source.y} 
                     ${target.x - dx * 0.5},${target.y} 
                     ${target.x},${target.y}`;
        })
        .attr("marker-end", "url(#arrow)");

    // 绘制节点组
    const node = g.selectAll(".node-group")
        .data(allNodes)
        .enter()
        .append("g")
        .attr("class", "node-group")
        .attr("transform", d => `translate(${d.x}, ${d.y})`)
        .on("click", (e, d) => {
            if (!d.isCenter) selectModel(d.id);
        })
        .on("mouseover", (e, d) => {
            // fill tooltip content
            tooltipEl.innerHTML = `
                <h4>${d.id}</h4>
                <p>类型: <span>${d.type}</span></p>
                <p>作者: <span>${d.author}</span></p>
                <p>任务: <span>${d.task}</span></p>
                <p>下载: <span>${d.downloads?.toLocaleString()}</span></p>
                <p>许可: <span>${d.license}</span></p>
                ${d.relation ? `<p>关系: <span>${d.relation}</span></p>` : ''}
                ${d.depth !== 0 ? `<p>层级: <span>${d.depth > 0 ? '下游' : '上游'} ${Math.abs(d.depth)}</span></p>` : ''}
            `;
            tooltipEl.style.opacity = 1;

            // 高亮相关连线
            link.style("stroke", l =>
                l.source === d.id || l.target === d.id ? "#61dafb" : "#333"
            ).style("stroke-opacity", l =>
                l.source === d.id || l.target === d.id ? 1 : 0.3
            );
        })
        .on("mousemove", (e) => {
            // Position tooltip relative to the .main container to account for sidebar offset
            const container = document.querySelector('.main');
            const rect = container.getBoundingClientRect();
            const x = e.clientX - rect.left + container.scrollLeft + 12;
            const y = e.clientY - rect.top + container.scrollTop + 12;
            // clamp to viewport within container
            const maxX = container.clientWidth - 10;
            const maxY = container.clientHeight - 10;
            tooltipEl.style.left = Math.min(x, maxX) + 'px';
            tooltipEl.style.top = Math.min(y, maxY) + 'px';
        })
        .on("mouseout", () => {
            tooltipEl.style.opacity = 0;
            link.style("stroke", "#333").style("stroke-opacity", 1);
        });

    // 节点圆圈
    node.append("circle")
        .attr("class", d => `node ${d.isCenter ? 'center' : ''}`)
        .attr("r", d => {
            if (d.isCenter) return 28;
            const baseSize = Math.max(8, 16 - Math.abs(d.depth) * 2);
            const popularityBonus = Math.min(6, ((d.downloads || 0) / 1000000));
            return baseSize + popularityBonus;
        })
        .attr("fill", d => {
            if (d.isCenter) return "#ffd700";
            if (d.type === 'dataset') return "#9d4edd";
            if (d.depth < 0) return "#ff6b6b";  // 上游 - 红色
            return "#61dafb";  // 下游 - 蓝色
        });

    // 节点标签
    node.append("text")
        .attr("class", "node-label")
        .attr("y", d => {
            const r = d.isCenter ? 28 : Math.max(8, 16 - Math.abs(d.depth) * 2) + 6;
            return r + 12;
        })
        .style("font-size", d => d.isCenter ? "12px" : `${Math.max(9, 11 - Math.abs(d.depth))}px`)
        .style("fill", d => d.isCenter ? "#ffd700" : "#888")
        .text(d => d.id.split('/').pop());
}

// 标签切换
document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(tab.dataset.tab + 'Panel').classList.add('active');
    });
});

// 深度切换
document.getElementById('depthSelect').addEventListener('change', (e) => {
    if (state.currentModel) {
        selectModel(state.currentModel);
    }
});

// 刷新
document.getElementById('refreshBtn').addEventListener('click', () => {
    if (state.currentModel) {
        selectModel(state.currentModel);
    }
});

// 窗口调整
window.addEventListener('resize', () => {
    const newWidth = window.innerWidth - 320;
    const newHeight = window.innerHeight;
    svg.attr("width", newWidth).attr("height", newHeight);
    if (state.lineageData) {
        renderGraph(state.lineageData);
    }
});

// 初始化检查
fetchAPI('/health').then(data => {
    if (data && !loadingDiv.empty()) {
        loadingDiv.text('搜索模型开始探索...');
    }
});
