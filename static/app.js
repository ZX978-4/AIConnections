// API配置
const API_BASE = 'http://localhost:5000/api';

// 状态
let state = {
    currentModel: null,
    depth: 99, // 默认展示最大层数
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

// relation -> color mapping (distinct from node colors)
function relationColor(relation) {
    if (!relation) return '#3b3b3b';
    // Convert hyphens to underscores to handle both formats
    const r = relation.toLowerCase().replace(/-/g, '_');
    // darker color palette for dark theme interface
    const map = {
        'trained_on': '#c0392b',   // dark red - distinct from upstream node color
        'based_on': '#2980b9',     // dark blue - distinct from downstream node color
        'fine_tune': '#7f8c8d',     // dark gray - as requested
        'quantization': '#34495e',  // dark blue - as requested
        'merge': '#27ae60',         // dark green - complementary color
        'adapter': '#16a085',       // dark teal - complementary color
        'distillation': '#2c3e50',  // darker blue-gray - complementary color
        'moe': '#5d6d7e'            // darker gray - distinct from fine_tune
    };
    return map[r] || '#3b3b3b';
}

// lighten hex color by percentage (0-100)
function lightenColor(hex, percent) {
    try {
        const clean = hex.replace('#', '').slice(0,6);
        const num = parseInt(clean, 16);
        let r = (num >> 16) & 0xFF;
        let g = (num >> 8) & 0xFF;
        let b = num & 0xFF;
        r = Math.min(255, Math.round(r + (255 - r) * (percent / 100)));
        g = Math.min(255, Math.round(g + (255 - g) * (percent / 100)));
        b = Math.min(255, Math.round(b + (255 - b) * (percent / 100)));
        return '#' + (r.toString(16).padStart(2, '0')) + (g.toString(16).padStart(2, '0')) + (b.toString(16).padStart(2, '0'));
    } catch (e) {
        return hex;
    }
}

// 切换图例显示/隐藏
function toggleLegend(id) {
    const content = document.getElementById(id);
    const header = content.previousElementSibling;
    const icon = header.querySelector('.toggle-icon');
    
    if (content.style.display === 'none' || content.style.display === '') {
        content.style.display = 'block';
        icon.textContent = '▲';
        icon.style.transform = 'rotate(180deg)';
    } else {
        content.style.display = 'none';
        icon.textContent = '▼';
        icon.style.transform = 'rotate(0deg)';
    }
}

// 在页面上渲染关系颜色图例，便于辨识
function renderRelationLegend() {
    const legendContainer = document.getElementById('edge-legend');
    if (!legendContainer) return;

    // 定义展示顺序与中文说明
    const legendItems = [
        { key: 'trained_on', label: 'trained_on（训练数据）' },
        { key: 'based_on', label: 'based_on（基础模型/来源）' },
        { key: 'fine_tune', label: 'fine_tune（微调）' },
        { key: 'quantization', label: 'quantization（量化）' },
        { key: 'merge', label: 'merge（模型合并）' },
        { key: 'adapter', label: 'adapter（适配器/插件）' },
        { key: 'distillation', label: 'distillation（蒸馏）' },
        { key: 'moe', label: 'moe（专家模型 MoE）' }
    ];

    // 清空现有内容
    legendContainer.innerHTML = '';

    // 插入每一项
    legendItems.forEach(item => {
        const el = document.createElement('div');
        el.className = 'legend-item relation-legend-item';
        el.setAttribute('data-relation', item.key);
        el.innerHTML = `<div class="legend-dot" style="background: ${relationColor(item.key)};"></div><span>${item.label}</span>`;
        legendContainer.appendChild(el);
    });
}

// 为图例项添加点击事件，实现过滤功能
function addLegendItemClickEvents() {
    const legendItems = document.querySelectorAll('.relation-legend-item');
    legendItems.forEach(item => {
        item.addEventListener('click', function() {
            const relation = this.getAttribute('data-relation');
            filterByRelation(relation);
        });
    });
}

// 保存原始图数据
let originalGraphData = null;

// 过滤显示指定关系的节点和连线
function filterByRelation(relation) {
    // 保存原始数据（如果还没有保存）
    if (!originalGraphData) {
        originalGraphData = {
            nodes: g.selectAll('.node-group').data(),
            links: g.selectAll('.link').data()
        };
    }
    
    // 隐藏所有节点和连线
    g.selectAll('.node-group').style('display', 'none');
    g.selectAll('.link').style('display', 'none');
    
    // 显示指定关系的连线
    const filteredLinks = g.selectAll('.link').filter(function(d) {
        return d.relation.toLowerCase().replace(/-/g, '_') === relation;
    });
    filteredLinks.style('display', 'block');
    
    // 收集需要显示的节点ID
    const nodeIdsToShow = new Set();
    filteredLinks.each(function(d) {
        nodeIdsToShow.add(d.source.id || d.source);
        nodeIdsToShow.add(d.target.id || d.target);
    });
    
    // 保留当前查询的节点
    if (state.currentModel) {
        nodeIdsToShow.add(state.currentModel);
    }
    
    // 构建图的邻接表，用于路径查找
    const adjacencyList = buildAdjacencyList();
    
    // 找出未被隐藏的节点与当前查询节点之间的路径上的所有节点
    if (state.currentModel) {
        const currentNodeId = state.currentModel;
        const nodesToCheck = Array.from(nodeIdsToShow);
        
        nodesToCheck.forEach(nodeId => {
            if (nodeId !== currentNodeId) {
                const path = findPath(adjacencyList, currentNodeId, nodeId);
                if (path) {
                    path.forEach(nodeInPath => {
                        nodeIdsToShow.add(nodeInPath);
                    });
                }
            }
        });
    }
    
    // 显示相关节点
    g.selectAll('.node-group').filter(function(d) {
        return nodeIdsToShow.has(d.id);
    }).style('display', 'block');
    
    // 显示连接这些节点的所有连线
    g.selectAll('.link').filter(function(d) {
        const sourceId = d.source.id || d.source;
        const targetId = d.target.id || d.target;
        return nodeIdsToShow.has(sourceId) && nodeIdsToShow.has(targetId);
    }).style('display', 'block');
    
    // 更新图例项的样式，标记当前选中的关系
    document.querySelectorAll('.relation-legend-item').forEach(item => {
        if (item.getAttribute('data-relation') === relation) {
            item.style.backgroundColor = 'rgba(50, 50, 50, 0.5)';
            item.style.borderRadius = '4px';
        } else {
            item.style.backgroundColor = 'transparent';
            item.style.borderRadius = '0';
        }
    });
}

// 构建图的邻接表
function buildAdjacencyList() {
    const adjacencyList = new Map();
    
    g.selectAll('.link').each(function(d) {
        const sourceId = d.source.id || d.source;
        const targetId = d.target.id || d.target;
        
        if (!adjacencyList.has(sourceId)) {
            adjacencyList.set(sourceId, []);
        }
        if (!adjacencyList.has(targetId)) {
            adjacencyList.set(targetId, []);
        }
        
        adjacencyList.get(sourceId).push(targetId);
        adjacencyList.get(targetId).push(sourceId);
    });
    
    return adjacencyList;
}

// 查找两个节点之间的路径（BFS算法）
function findPath(adjacencyList, start, end) {
    if (start === end) return [start];
    
    const visited = new Set();
    const queue = [[start]];
    
    while (queue.length > 0) {
        const path = queue.shift();
        const current = path[path.length - 1];
        
        if (visited.has(current)) continue;
        visited.add(current);
        
        const neighbors = adjacencyList.get(current) || [];
        for (const neighbor of neighbors) {
            if (neighbor === end) {
                return [...path, neighbor];
            }
            if (!visited.has(neighbor)) {
                queue.push([...path, neighbor]);
            }
        }
    }
    
    return null;
}

// 重置过滤器，显示所有节点和连线
function resetFilter() {
    // 显示所有节点和连线
    g.selectAll('.node-group').style('display', 'block');
    g.selectAll('.link').style('display', 'block');
    
    // 清除图例项的选中状态
    document.querySelectorAll('.relation-legend-item').forEach(item => {
        item.style.backgroundColor = 'transparent';
        item.style.borderRadius = '0';
    });
    
    // 清除原始数据
    originalGraphData = null;
}

// 为图例添加重置按钮
function addResetButton() {
    const edgeLegend = document.getElementById('edge-legend');
    if (edgeLegend) {
        const resetButton = document.createElement('div');
        resetButton.className = 'legend-item reset-button';
        resetButton.style.cursor = 'pointer';
        resetButton.style.fontWeight = 'bold';
        resetButton.style.marginTop = '10px';
        resetButton.style.paddingTop = '10px';
        resetButton.style.borderTop = '1px solid #333';
        resetButton.textContent = '重置显示';
        resetButton.addEventListener('click', resetFilter);
        edgeLegend.appendChild(resetButton);
    }
}

// 重新渲染关系图例并添加点击事件
function renderRelationLegendWithEvents() {
    renderRelationLegend();
    addLegendItemClickEvents();
    addResetButton();
}

// 替换原来的renderRelationLegend调用
renderRelationLegendWithEvents();

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

function renderSearchResults(results) {
    const container = document.getElementById('searchResults');
    if (results.length === 0) {
        container.innerHTML = '<div class="search-item">未找到匹配的模型或数据集</div>';
    } else {
        container.innerHTML = results.map(item => `
          <div class="search-item" data-model="${item}">
            <div>${item}</div>
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
    const depth = state.depth;

    // 加载血缘数据
    const data = await fetchAPI(`/model/${encodeURIComponent(modelId)}/lineage?depth=${depth}`);
    if (!data) return;

    state.lineageData = data;

    // 更新UI
    updateSidebar(data);
    updateInfoBar(data.model);
    renderGraph(data);
    // 重新渲染图例并添加点击事件
    setTimeout(renderRelationLegendWithEvents, 100);
}

// 加载下载量前20的模型
async function loadTopDownloads() {
    try {
        const models = await fetchAPI('/models/top-downloads');
        if (models) {
            renderModelList(models, 'top-downloadsPanel', 'topDownloadsLoading');
        }
    } catch (e) {
        console.error('加载下载量Top20模型失败:', e);
        document.getElementById('topDownloadsLoading').textContent = '加载失败';
    }
}

// 加载最热门的20个数据集
async function loadTopDatasets() {
    try {
        const datasets = await fetchAPI('/datasets/top');
        if (datasets) {
            renderModelList(datasets, 'top-datasetsPanel', 'topDatasetsLoading');
        }
    } catch (e) {
        console.error('加载最热门数据集失败:', e);
        document.getElementById('topDatasetsLoading').textContent = '加载失败';
    }
}

// 渲染模型列表
function renderModelList(models, containerId, loadingId) {
    const container = document.getElementById(containerId);
    const loading = document.getElementById(loadingId);
    
    if (!container) return;
    
    // 隐藏加载提示
    if (loading) {
        loading.style.display = 'none';
    }
    
    // 清空容器
    container.innerHTML = '';
    
    // 渲染模型列表
    models.forEach(model => {
        const modelCard = document.createElement('div');
        modelCard.className = 'relation-card';
        modelCard.setAttribute('data-model', model.id);
        modelCard.innerHTML = `
            <div class="title">${model.id}</div>
            <div class="meta">${model.author || 'Unknown'} · ${formatDownloads(model.downloads)}</div>
            <span class="badge">${model.task}</span>
        `;
        container.appendChild(modelCard);
    });
}

// 为模型列表容器添加事件委托（只绑定一次）
function setupModelListEventListeners() {
    // 为下载量Top20面板添加事件委托
    const topDownloadsPanel = document.getElementById('top-downloadsPanel');
    if (topDownloadsPanel) {
        topDownloadsPanel.addEventListener('click', function(e) {
            const card = e.target.closest('.relation-card');
            if (card) {
                selectModel(card.dataset.model);
            }
        });
    }
    
    // 为最热门数据集面板添加事件委托
    const topDatasetsPanel = document.getElementById('top-datasetsPanel');
    if (topDatasetsPanel) {
        topDatasetsPanel.addEventListener('click', function(e) {
            const card = e.target.closest('.relation-card');
            if (card) {
                selectModel(card.dataset.model);
            }
        });
    }
}

function updateSidebar(data) {
    // 清除先前的检测结果（切换模型时避免混淆）
    const licenseResultEl = document.getElementById('licenseResult');
    if (licenseResultEl) licenseResultEl.innerHTML = '';
    const riskResultEl = document.getElementById('riskResult');
    if (riskResultEl) riskResultEl.innerHTML = '';
    // 当前模型
    document.getElementById('currentModelSection').style.display = 'block';
    document.getElementById('currentModelName').textContent = data.model.id;
    document.getElementById('currentModelMeta').textContent = `${data.model.author} · ${data.model.task} · ${formatDownloads(data.model.downloads)}`;

    // 统计
    document.getElementById('statAncestors').textContent = data.stats.ancestors_count;
    document.getElementById('statDescendants').textContent = data.stats.descendants_count;
    // statTotal element removed from UI
    // statDepth element removed from UI

    // 卡片点击事件已在renderModelList函数中处理，无需重复绑定

    // 绑定证书检测按钮
    const licenseBtn = document.getElementById('licenseBtn');
    const licenseResult = document.getElementById('licenseResult');
    if (licenseBtn) {
        licenseBtn.onclick = async () => {
            if (!state.currentModel) return;
            licenseBtn.disabled = true;
            licenseResult.textContent = '正在检测证书冲突...';
            try {
                await runLicenseCheck(state.currentModel);
            } catch (e) {
                licenseResult.textContent = '证书检测失败: ' + e.message;
            }
            licenseBtn.disabled = false;
        }
    }
    
    // 绑定安全检测按钮
    const riskBtn = document.getElementById('riskBtn');
    const riskResult = document.getElementById('riskResult');
    if (riskBtn) {
        riskBtn.onclick = async () => {
            if (!state.currentModel) return;
            riskBtn.disabled = true;
            riskResult.textContent = '正在进行安全检测...';
            try {
                await runRiskCheck(state.currentModel);
            } catch (e) {
                riskResult.textContent = '安全检测失败: ' + e.message;
            }
            riskBtn.disabled = false;
        }
    }
    
    // 绑定导出供应链按钮
    const exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.onclick = async () => {
            if (!state.currentModel) return;
            exportBtn.disabled = true;
            try {
                await exportSupplyChain(state.currentModel);
            } catch (e) {
                console.error('导出失败:', e);
            }
            exportBtn.disabled = false;
        }
    }
}

// HTML转义辅助
function escapeHtml(str) {
    if (!str && str !== 0) return '';
    return String(str).replace(/[&<>"'`]/g, function (s) {
        return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;','`':'&#96;'})[s];
    });
}

// 证书冲突检测：请求后端 /license_check 并展示结果
async function runLicenseCheck(modelId) {
    const licenseResult = document.getElementById('licenseResult');
    licenseResult.innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/model/${encodeURIComponent(modelId)}/license_check`);
        if (!res.ok) {
            const txt = await res.text();
            licenseResult.textContent = '后端返回错误: ' + res.status + ' ' + txt;
            return;
        }
        const json = await res.json();

        // 渲染结构化结果
        let html = `<div style="font-weight:600;">许可检测: ${escapeHtml(json.status || '-')}</div>`;
        if (json.model_license) html += `<div>模型许可: <strong>${escapeHtml(json.model_license)}</strong></div>`;
        if (Array.isArray(json.upstream) && json.upstream.length>0) {
            html += `<div style="margin-top:6px;font-size:12px;color:#ddd;"><strong>上游许可摘要：</strong><ul style='margin:6px 0 6px 16px;padding:0;color:#ddd'>`;
            json.upstream.forEach(u => {
                html += `<li>${escapeHtml(u.id)} — ${escapeHtml(u.license || '未知')} ${u.conflict ? '<span style="color:#ff9b9b;font-weight:600;margin-left:6px">冲突</span>' : ''}</li>`;
            });
            html += `</ul></div>`;
        }
        if (Array.isArray(json.conflicts) && json.conflicts.length>0) {
            html += `<div style="margin-top:6px;color:#ffb86b;font-size:12px"><strong>检测到 ${json.conflicts.length} 处冲突：</strong><ul style='margin:6px 0 6px 16px;padding:0'>`;
            json.conflicts.forEach(c => {
                html += `<li>${escapeHtml(c)}</li>`;
            });
            html += `</ul></div>`;
        } else {
            html += `<div style="margin-top:6px;color:#9ad1a0;font-size:12px">未发现明显许可冲突。</div>`;
        }

        licenseResult.innerHTML = html;
    } catch (e) {
        licenseResult.textContent = '证书检测出错: ' + e.message;
    }
}

// 安全风险检测：请求后端 /risk_check 并展示结果
async function runRiskCheck(modelId) {
    const riskResult = document.getElementById('riskResult');
    riskResult.innerHTML = '';

    try {
        const res = await fetch(`${API_BASE}/model/${encodeURIComponent(modelId)}/risk_check`);
        if (!res.ok) {
            const txt = await res.text();
            riskResult.textContent = '后端返回错误: ' + res.status + ' ' + txt;
            return;
        }
        const json = await res.json();

        // 渲染结构化结果
        let html = `<div style="font-weight:600;">安全检测: ${escapeHtml(json.risk_level || '-')}</div>`;
        html += `<div style="margin-top:6px;font-size:12px;">原因: ${escapeHtml(json.reason || '无')}</div>`;

        riskResult.innerHTML = html;
    } catch (e) {
        riskResult.textContent = '安全检测出错: ' + e.message;
    }
}

// 导出供应链数据
async function exportSupplyChain(modelId) {
    try {
        // 获取选择的导出类型
        const exportType = document.getElementById('exportType').value;
        
        if (exportType === 'json') {
            // 导出为JSON
            await exportAsJson(modelId);
        } else if (exportType === 'png') {
            // 导出为PNG图片
            exportAsPng(modelId);
        } else if (exportType === 'svg') {
            // 导出为SVG矢量图
            exportAsSvg(modelId);
        }
    } catch (e) {
        console.error('导出失败:', e);
        alert('导出失败: ' + e.message);
    }
}

// 导出为JSON
async function exportAsJson(modelId) {
    try {
        // 获取当前模型的供应链数据
        const res = await fetch(`${API_BASE}/model/${encodeURIComponent(modelId)}/lineage?depth=99`);
        if (!res.ok) {
            const txt = await res.text();
            alert('导出失败: ' + res.status + ' ' + txt);
            return;
        }
        const data = await res.json();

        // 准备导出数据
        const exportData = {
            model: data.model,
            ancestors: data.ancestors,
            descendants: data.descendants,
            stats: data.stats,
            export_time: new Date().toISOString()
        };

        // 创建JSON文件并下载
        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${modelId.split('/').pop()}_supply_chain.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // 显示成功消息
        alert('供应链数据已成功导出为JSON');
    } catch (e) {
        console.error('导出失败:', e);
        alert('导出失败: ' + e.message);
    }
}

// 导出为PNG图片
function exportAsPng(modelId) {
    try {
        // 获取SVG元素
        const svg = document.querySelector('#graph svg');
        if (!svg) {
            alert('未找到图形元素');
            return;
        }
        
        // 克隆SVG元素，确保导出完整的图形
        const clonedSvg = svg.cloneNode(true);
        
        // 确保克隆的SVG有正确的尺寸
        clonedSvg.setAttribute('width', svg.clientWidth);
        clonedSvg.setAttribute('height', svg.clientHeight);
        
        // 转换SVG为XML字符串
        const svgData = new XMLSerializer().serializeToString(clonedSvg);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);
        
        // 创建图像对象
        const img = new Image();
        img.onload = function() {
            // 创建Canvas元素
            const canvas = document.createElement('canvas');
            canvas.width = svg.clientWidth;
            canvas.height = svg.clientHeight;
            
            // 绘制图像到Canvas
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#121212'; // 背景色
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            
            // 转换Canvas为PNG并下载
            canvas.toBlob(function(blob) {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${modelId.split('/').pop()}_supply_chain.png`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                // 显示成功消息
                alert('供应链图形已成功导出为PNG');
            }, 'image/png');
            
            // 释放URL
            URL.revokeObjectURL(url);
        };
        
        // 设置图像源
        img.src = url;
    } catch (e) {
        console.error('导出失败:', e);
        alert('导出失败: ' + e.message);
    }
}

// 导出为SVG矢量图
function exportAsSvg(modelId) {
    try {
        // 获取SVG元素
        const svg = document.querySelector('#graph svg');
        if (!svg) {
            alert('未找到图形元素');
            return;
        }
        
        // 克隆SVG元素，确保导出完整的图形
        const clonedSvg = svg.cloneNode(true);
        
        // 确保克隆的SVG有正确的尺寸
        clonedSvg.setAttribute('width', svg.clientWidth);
        clonedSvg.setAttribute('height', svg.clientHeight);
        
        // 转换SVG为XML字符串
        const svgData = new XMLSerializer().serializeToString(clonedSvg);
        const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
        const url = URL.createObjectURL(svgBlob);
        
        // 创建下载链接
        const a = document.createElement('a');
        a.href = url;
        a.download = `${modelId.split('/').pop()}_supply_chain.svg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        // 显示成功消息
        alert('供应链图形已成功导出为SVG');
    } catch (e) {
        console.error('导出失败:', e);
        alert('导出失败: ' + e.message);
    }
}

function updateInfoBar(model) {
    document.getElementById('infoBar').style.display = 'flex';
    document.getElementById('infoName').textContent = model.id;
    document.getElementById('infoAuthor').textContent = model.author || 'Unknown';
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
    // helper: relation -> dash pattern
    function relationDash(relation) {
        // All relations use solid lines as requested
        return '';
    }

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
        .attr("marker-end", "url(#arrow)")
    .attr("stroke", d => relationColor(d.relation))
    .attr("stroke-width", d => 2.2)
    .attr("stroke-linecap", "round")
    .attr("stroke-dasharray", d => relationDash(d.relation))
    .style("stroke-opacity", 0.95);

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

            // 高亮相关连线（使用 relationColor 的浅化版本）
            link.style("stroke", l => {
                const base = relationColor(l.relation);
                if (l.source === d.id || l.target === d.id) {
                    // use a lightened version of the relation color for highlight
                    return lightenColor(base, 45);
                }
                return base;
            }).style("stroke-opacity", l =>
                l.source === d.id || l.target === d.id ? 1 : 0.18
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
            // 恢复每条连线的原始 relation 颜色
            link.style("stroke", l => relationColor(l.relation)).style("stroke-opacity", 0.9);
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
            if (d.isCenter) return "#ffeb3b";  // light gold - distinct from relation colors
            if (d.type === 'dataset') return "#ba68c8";  // light purple - distinct from relation colors
            if (d.depth < 0) return "#ff8a80";  // light red - distinct from relation colors
            return "#81d4fa";  // light blue - distinct from relation colors
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
        .text(d => d.id);
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
// depthSelect control removed; depth is fixed to show maximum by default



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

// 页面加载时加载热门模型和数据集列表，并设置事件监听器
window.addEventListener('load', function() {
    loadTopDownloads();
    loadTopDatasets();
    setupModelListEventListeners();
});
