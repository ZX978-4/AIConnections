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

// relation -> muted dark color mapping
function relationColor(relation) {
    if (!relation) return '#3b3b3b';
    const r = relation.toLowerCase();
    // clearer muted palette for better visual distinction
    const map = {
        'trained_on': '#3b3b3b', // dark gray
        'based_on': '#3f5160',   // muted slate
        'fine_tune': '#5a3b3b',   // muted maroon
        'quantization': '#4a4a29',// muted olive
        'merge': '#473547',       // muted plum
        'adapter': '#2f5047',     // muted teal
        'distillation': '#4a4f3f',// muted moss
        'moe': '#3a3a3a'          // neutral dark
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

// 在页面上渲染关系颜色图例，便于辨识
function renderRelationLegend() {
    const legendContainer = document.querySelector('.legend');
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

    // 在现有图例前插入关系图例标题
    const header = document.createElement('div');
    header.className = 'legend-title';
    header.textContent = '关系颜色 (relation)';
    legendContainer.insertBefore(header, legendContainer.firstChild);

    // 插入每一项
    legendItems.forEach(item => {
        const el = document.createElement('div');
        el.className = 'legend-item relation-legend-item';
        el.innerHTML = `<div class="legend-dot" style="background: ${relationColor(item.key)};"></div><span>${item.label}</span>`;
        legendContainer.insertBefore(el, header.nextSibling);
    });
}

// 渲染一次关系图例
renderRelationLegend();

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
    // 清除先前的证书检测结果（切换模型时避免混淆）
    const licenseResultEl = document.getElementById('licenseResult');
    if (licenseResultEl) licenseResultEl.innerHTML = '';
    // 当前模型
    document.getElementById('currentModelSection').style.display = 'block';
    document.getElementById('currentModelName').textContent = data.model.id.split('/').pop();
    document.getElementById('currentModelMeta').textContent = `${data.model.author} · ${data.model.task} · ${formatDownloads(data.model.downloads)}`;

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
    // helper: relation -> dash pattern
    function relationDash(relation) {
        const r = (relation || '').toLowerCase();
        const map = {
            'trained_on': '',        // solid
            'based_on': '6 3',       // long dash
            'fine_tune': '4 3',      // medium dash
            'quantization': '2 4',   // dotted-ish
            'merge': '8 4 2 4',      // complex
            'adapter': '3 3',        // short dash
            'distillation': '2 6',   // sparse dots
            'moe': ''                // solid
        };
        return map[r] || '';
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
