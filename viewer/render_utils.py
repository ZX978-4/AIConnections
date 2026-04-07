import json
import networkx as nx


def generate_d3_html(
    G,
    center_node=None,
    layout_type="spring",
    expanded_nodes=None,
    show_labels=True,
    show_edge_labels=False,
    arrow_enabled=True,
    highlight_center=True,
):
    if layout_type == "spring":
        pos = nx.spring_layout(G, k=3, iterations=100, seed=42)
    elif layout_type == "circular":
        pos = nx.circular_layout(G)
    elif layout_type == "kamada_kawai":
        try:
            pos = nx.kamada_kawai_layout(G)
        except Exception:
            pos = nx.spring_layout(G, k=3, iterations=100, seed=42)
    elif layout_type == "hierarchical":
        try:
            pos = nx.multipartite_layout(G, subset_key="layer")
        except Exception:
            pos = nx.spring_layout(G, k=3, iterations=100, seed=42)
    else:
        pos = nx.random_layout(G, seed=42)

    nodes = []
    color_map = {
        "model": "#61DAFB",
        "dataset": "#9D4EDD",
        "code": "#00FF88",
        "agent": "#FF6B6B",
        "unknown": "#CCCCCC",
    }

    if layout_type == "hierarchical" and center_node is not None:
        try:
            for node_id in G.nodes():
                if node_id == center_node:
                    G.nodes[node_id]["layer"] = 0
                else:
                    try:
                        dist = nx.shortest_path_length(G, source=center_node, target=node_id)
                        G.nodes[node_id]["layer"] = dist
                    except Exception:
                        G.nodes[node_id]["layer"] = 1
        except Exception:
            pass

    for node_id in G.nodes():
        node_data = G.nodes[node_id]
        x, y = pos[node_id]
        if center_node and node_id == center_node and highlight_center:
            size = 45
        else:
            downloads = node_data.get("downloads", 0)
            size = min(30, max(12, 12 + downloads / 200000))

        node_type = node_data.get("type", "unknown")
        if center_node and node_id == center_node and highlight_center:
            color = "#FFD700"
        elif expanded_nodes and node_id in expanded_nodes:
            color = "#FF6B6B"
        else:
            color = color_map.get(node_type, "#CCCCCC")

        label = node_id.split("/")[-1] if show_labels else ""
        children_count = len(list(G.successors(node_id)))
        hover_text = f"""
        <b>{node_id}</b><br>
        Type: {node_type}<br>
        Author: {node_data.get('author', 'unknown')}<br>
        Params: {node_data.get('params', '-') }<br>
        Downloads: {node_data.get('downloads', 0):,}<br>
        License: {node_data.get('license', 'unknown')}<br>
        Children: {children_count}
        """

        nodes.append(
            {
                "id": node_id,
                "x": x * 600,
                "y": y * 600,
                "size": size,
                "color": color,
                "label": label,
                "hover_text": hover_text,
                "type": node_type,
                "has_children": children_count > 0,
                "children_count": children_count,
                "is_center": (node_id == center_node),
            }
        )

    edges = []
    for source, target in G.edges():
        edge_data = G.edges[source, target]
        edges.append(
            {
                "source": source,
                "target": target,
                "relation": edge_data.get("relation", ""),
                "show_label": show_edge_labels,
            }
        )

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    expanded_nodes_json = json.dumps(list(expanded_nodes)) if expanded_nodes else "[]"
    title_text = (
        f"Model Lineage Graph (center: {center_node})"
        if center_node
        else "Global Model Lineage Graph"
    )

    d3_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <script src="https://d3js.org/d3.v7.min.js"></script>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ background-color: #0E1117; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
            #graph-container {{ width: 100%; height: 750px; position: relative; overflow: hidden; }}
            svg {{ width: 100%; height: 100%; }}
            .link {{ stroke: #888888; stroke-width: 1.5; stroke-opacity: 0.8; fill: none; }}
            .link-label {{ fill: #FAFAFA; font-size: 10px; text-anchor: middle; }}
            .node {{ cursor: pointer; stroke: #FFFFFF; stroke-width: 2; stroke-opacity: 0.9; }}
            .node-label {{ fill: #FAFAFA; font-size: 10px; text-anchor: middle; pointer-events: none; }}
            .tooltip {{
                position: absolute;
                background: #1E2230;
                color: #FAFAFA;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #61DAFB;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.2s;
                font-size: 12px;
                z-index: 1000;
                max-width: 300px;
            }}
            .arrow-marker {{ fill: #888888; }}
            h3 {{ color: #61DAFB; position: absolute; top: 10px; left: 10px; z-index: 100; margin: 0; }}
            .controls {{
                position: absolute;
                top: 10px;
                right: 10px;
                z-index: 100;
                background: #1E2230;
                padding: 10px;
                border-radius: 8px;
                border: 1px solid #61DAFB;
            }}
            .control-btn {{
                background: #61DAFB;
                color: #0E1117;
                border: none;
                padding: 5px 10px;
                margin: 2px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }}
            .control-btn:hover {{ background: #4F46E5; color: white; }}
            .expand-indicator {{
                fill: #FF6B6B;
                font-size: 14px;
                font-weight: bold;
                pointer-events: none;
            }}
        </style>
    </head>
    <body>
        <div id="graph-container">
            <h3>{title_text}</h3>
            <div class="controls">
                <button class="control-btn" onclick="expandAll()">Expand All</button>
                <button class="control-btn" onclick="collapseAll()">Collapse All</button>
                <button class="control-btn" onclick="resetZoom()">Reset View</button>
            </div>
            <div class="tooltip" id="tooltip"></div>
        </div>

        <script>
            const nodes = {nodes_json};
            const edges = {edges_json};
            const expandedNodes = {expanded_nodes_json};
            const arrowEnabled = {str(arrow_enabled).lower()};
            const centerNode = "{center_node if center_node else ''}";
            const showEdgeLabels = {str(show_edge_labels).lower()};
            const showLabels = {str(show_labels).lower()};

            const container = document.getElementById('graph-container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            const tooltip = document.getElementById('tooltip');

            const svg = d3.select('#graph-container')
                .append('svg')
                .attr('width', width)
                .attr('height', height);

            const zoom = d3.zoom()
                .scaleExtent([0.1, 10])
                .on('zoom', (event) => {{
                    g.attr('transform', event.transform);
                }});
            svg.call(zoom);

            if (arrowEnabled) {{
                svg.append('defs').append('marker')
                    .attr('id', 'arrow')
                    .attr('viewBox', '0 -5 10 10')
                    .attr('refX', 20)
                    .attr('refY', 0)
                    .attr('markerWidth', 8)
                    .attr('markerHeight', 8)
                    .attr('orient', 'auto')
                    .append('path')
                    .attr('d', 'M0,-5L10,0L0,5')
                    .attr('class', 'arrow-marker');
            }}

            const g = svg.append('g')
                .attr('transform', `translate(${{width/2}}, ${{height/2}})`);

            const nodeMap = new Map(nodes.map(n => [n.id, n]));

            const link = g.selectAll('.link')
                .data(edges)
                .enter()
                .append('path')
                .attr('class', 'link')
                .attr('d', d => {{
                    const source = nodeMap.get(d.source);
                    const target = nodeMap.get(d.target);
                    return `M${{source.x}},${{source.y}} L${{target.x}},${{target.y}}`;
                }})
                .attr('marker-end', arrowEnabled ? 'url(#arrow)' : '');

            if (showEdgeLabels) {{
                g.selectAll('.link-label')
                    .data(edges)
                    .enter()
                    .append('text')
                    .attr('class', 'link-label')
                    .attr('x', d => {{
                        const source = nodeMap.get(d.source);
                        const target = nodeMap.get(d.target);
                        return (source.x + target.x) / 2;
                    }})
                    .attr('y', d => {{
                        const source = nodeMap.get(d.source);
                        const target = nodeMap.get(d.target);
                        return (source.y + target.y) / 2 - 5;
                    }})
                    .text(d => d.relation);
            }}

            const nodeGroup = g.selectAll('.node-group')
                .data(nodes)
                .enter()
                .append('g')
                .attr('class', 'node-group')
                .attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);

            const node = nodeGroup.append('circle')
                .attr('class', 'node')
                .attr('r', d => d.size)
                .attr('fill', d => d.color)
                .attr('stroke', d => d.is_center ? '#FFD700' : '#FFFFFF')
                .attr('stroke-width', d => d.is_center ? 4 : 2);

            nodeGroup.filter(d => d.has_children)
                .append('circle')
                .attr('class', 'expand-indicator')
                .attr('r', 4)
                .attr('cx', d => d.size * 0.7)
                .attr('cy', d => -d.size * 0.7)
                .attr('fill', '#FF6B6B');

            nodeGroup
                .on('mouseover', function(event, d) {{
                    d3.select(this).select('.node').attr('stroke-width', 4).attr('stroke', '#61DAFB');
                    link.style('stroke-opacity', l =>
                        l.source === d.id || l.target === d.id ? 1 : 0.2
                    );
                    link.style('stroke', l =>
                        l.source === d.id || l.target === d.id ? '#61DAFB' : '#888888'
                    );
                    tooltip.style('opacity', 1)
                        .html(d.hover_text)
                        .style('left', (event.pageX + 10) + 'px')
                        .style('top', (event.pageY + 10) + 'px');
                }})
                .on('mousemove', (event) => {{
                    tooltip.style('left', (event.pageX + 10) + 'px')
                        .style('top', (event.pageY + 10) + 'px');
                }})
                .on('mouseout', function(event, d) {{
                    d3.select(this).select('.node')
                        .attr('stroke-width', d.is_center ? 4 : 2)
                        .attr('stroke', d.is_center ? '#FFD700' : '#FFFFFF');
                    link.style('stroke-opacity', 0.8);
                    link.style('stroke', '#888888');
                    tooltip.style('opacity', 0);
                }})
                .on('click', (event, d) => {{
                    event.stopPropagation();
                    const rootWindow = window.parent;
                    const inputEl = rootWindow.document.getElementById('clicked_node');
                    if (inputEl) {{
                        inputEl.value = d.id;
                        inputEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        inputEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }})
                .on('dblclick', (event, d) => {{
                    event.stopPropagation();
                    const rootWindow = window.parent;
                    const expandEl = rootWindow.document.getElementById('expand_node');
                    if (expandEl) {{
                        expandEl.value = d.id;
                        expandEl.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        expandEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    }}
                }});

            if (showLabels) {{
                nodeGroup.append('text')
                    .attr('class', 'node-label')
                    .attr('y', d => d.size + 12)
                    .text(d => d.label);
            }}

            window.expandAll = function() {{
                const rootWindow = window.parent;
                const btn = rootWindow.document.getElementById('expand_all_btn');
                if (btn) btn.click();
            }};

            window.collapseAll = function() {{
                const rootWindow = window.parent;
                const btn = rootWindow.document.getElementById('collapse_all_btn');
                if (btn) btn.click();
            }};

            window.resetZoom = function() {{
                svg.transition().duration(750).call(
                    zoom.transform,
                    d3.zoomIdentity.translate(width/2, height/2).scale(1)
                );
            }};

            window.exportPNG = async function() {{
                const canvas = await html2canvas(container);
                const link = document.createElement('a');
                link.download = 'model_lineage.png';
                link.href = canvas.toDataURL();
                link.click();
            }};

            window.exportHTML = function() {{
                const htmlContent = document.documentElement.outerHTML;
                const blob = new Blob([htmlContent], {{type: 'text/html'}});
                const link = document.createElement('a');
                link.download = 'model_lineage.html';
                link.href = URL.createObjectURL(blob);
                link.click();
            }};
        </script>
    </body>
    </html>
    """
    return d3_html
