import json
import os

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(page_title="Fujairah Slick Evolution 2025", layout="wide")

st.markdown(
    """
    <style>
        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > .main,
        [data-testid="stHeader"] {
            background: #0b1220 !important;
            color: #e5eefb !important;
        }
        header[data-testid="stHeader"],
        div[data-testid="stToolbar"],
        div[data-testid="stDecoration"] {
            display: none;
        }
        [data-testid="stSidebar"],
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none;
        }
        .block-container {
            padding-top: 2rem;
        }
        div[data-testid="stButton"] > button {
            width: 100%;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.08);
            color: #e5eefb;
            font-weight: 700;
            padding: 0.85rem 0;
        }
        div[data-testid="stButton"] > button:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.16);
        }
    </style>
    """,
    unsafe_allow_html=True,
)

nav_left, nav_right = st.columns(2)
with nav_left:
    if st.button("Map", use_container_width=True):
        st.switch_page("app.py")
with nav_right:
    if st.button("Analysis", use_container_width=True):
        st.switch_page("pages/2_Analysis.py")

st.title("Fujairah Slick Evolution 2025")

HEX_FILE = "hex_heatmap.json"
SHAPES_FILE = "simplified_shapes.json"
SHAPE_HEATMAP_FILE = "shape_heatmap_grid.json"
EEZ_FILE = "alfujairah_eez.geojson"

if not all(os.path.exists(path) for path in [HEX_FILE, SHAPES_FILE, SHAPE_HEATMAP_FILE, EEZ_FILE]):
    st.error("Data files not found. Please run the pre-calculation scripts first.")
    st.stop()

with open(HEX_FILE, "r") as f:
    hex_data = json.load(f)
with open(SHAPES_FILE, "r") as f:
    all_shapes = json.load(f)
with open(SHAPE_HEATMAP_FILE, "r") as f:
    shape_heatmap_data = json.load(f)
with open(EEZ_FILE, "r") as f:
    eez_geojson = json.load(f)

hex_features = hex_data.get("features", [])
hex_meta = hex_data.get("meta", {})
eez_bounds = hex_meta.get("bounds", [56.26971221, 24.98042703, 57.12739197, 25.69296799])

html_code = f"""
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/deck.gl@latest/dist.min.js"></script>
    <script src="https://unpkg.com/@deck.gl/aggregation-layers@latest/dist.min.js"></script>
    <script src="https://unpkg.com/@deck.gl/geo-layers@latest/dist.min.js"></script>
    <style>
        :root {{
            --panel-bg: rgba(10, 14, 20, 0.94);
            --panel-border: rgba(255, 255, 255, 0.08);
            --text: #e8eef7;
            --muted: #9fb0c4;
            --accent: #2dd4bf;
            --accent-2: #38bdf8;
        }}
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background:
                radial-gradient(circle at top left, rgba(45, 212, 191, 0.12), transparent 30%),
                radial-gradient(circle at bottom right, rgba(56, 189, 248, 0.14), transparent 28%),
                #05070b;
            font-family: "Segoe UI", Arial, sans-serif;
        }}
        #container {{ width: 100vw; height: 100vh; }}
        #controls {{
            position: absolute;
            top: 18px;
            left: 18px;
            z-index: 10;
            width: 320px;
            color: var(--text);
            background: var(--panel-bg);
            border: 1px solid var(--panel-border);
            border-radius: 16px;
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.35);
            backdrop-filter: blur(10px);
            padding: 16px;
        }}
        .month-display {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 10px;
            color: white;
        }}
        .subtitle {{
            font-size: 12px;
            color: var(--muted);
            margin-bottom: 12px;
            line-height: 1.4;
        }}
        .play-btn {{
            background: linear-gradient(135deg, var(--accent), var(--accent-2));
            border: none;
            color: #031017;
            padding: 10px 16px;
            border-radius: 10px;
            cursor: pointer;
            width: 100%;
            font-size: 15px;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        .play-btn:hover {{ filter: brightness(1.05); }}
        #slider {{ width: 100%; margin-top: 8px; cursor: pointer; accent-color: var(--accent); }}
        .checkbox-group {{
            background: rgba(255,255,255,0.04);
            padding: 10px;
            border-radius: 12px;
            margin-top: 12px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .mode-group {{
            background: rgba(255,255,255,0.04);
            padding: 10px;
            border-radius: 12px;
            margin-top: 12px;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .checkbox-container, .mode-container {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 13px;
            font-weight: 600;
            color: var(--text);
        }}
        .mode-container input, .checkbox-container input {{
            margin-right: 10px;
            width: 16px;
            height: 16px;
            cursor: pointer;
        }}
        .legend {{
            display: grid;
            grid-template-columns: 1fr auto;
            gap: 10px;
            align-items: center;
            margin-top: 12px;
            padding: 10px;
            border-radius: 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .legend-bar {{
            height: 12px;
            border-radius: 999px;
            background: linear-gradient(90deg, #08306b, #08519c, #2b8cbe, #7bccc4, #c7e9b4, #fecc5c, #fd8d3c, #e31a1c);
            border: 1px solid rgba(255,255,255,0.12);
        }}
        .legend-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: var(--muted);
            margin-top: 4px;
        }}
        #stats {{
            margin-top: 12px;
            padding: 12px;
            border-radius: 12px;
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            font-size: 13px;
            line-height: 1.55;
        }}
        #stats strong {{ color: white; }}
        .stat-muted {{ color: var(--muted); }}
    </style>
</head>
<body>
    <div id="controls">
        <div id="month-name" class="month-display">January 2025</div>
        <div class="subtitle">
            The month slider controls time. Heat colors can switch between yearly, monthly, and cumulative overlap.
        </div>
        <button id="play-btn" class="play-btn">Play Animation</button>
        <input type="range" id="slider" min="1" max="12" value="1" step="1">

        <div class="mode-group">
            <div class="checkbox-container" style="margin-bottom: 6px;">
                <span>Heatmap mode</span>
            </div>
            <div class="mode-container">
                <input type="radio" id="mode-yearly" name="heat-mode" value="yearly" checked>
                <label for="mode-yearly">Yearly</label>
            </div>
            <div class="mode-container">
                <input type="radio" id="mode-monthly" name="heat-mode" value="monthly">
                <label for="mode-monthly">Monthly</label>
            </div>
            <div class="mode-container">
                <input type="radio" id="mode-cumulative" name="heat-mode" value="cumulative">
                <label for="mode-cumulative">Cumulative</label>
            </div>
        </div>

        <div class="checkbox-group">
            <div class="checkbox-container">
                <input type="checkbox" id="heatmap-cb" checked>
                <label for="heatmap-cb">Show Hex Heatmap</label>
            </div>
            <div class="checkbox-container">
                <input type="checkbox" id="shapes-cb" checked>
                <label for="shapes-cb">Show Slick Shapes</label>
            </div>
            <div class="checkbox-container">
                <input type="checkbox" id="shape-heatmap-cb" checked>
                <label for="shape-heatmap-cb">Show Shape Heatmap</label>
            </div>
        </div>

        <div class="legend">
            <div>
                <div class="legend-bar"></div>
                <div class="legend-labels">
                    <span>Low annual overlap</span>
                    <span>High annual overlap</span>
                </div>
            </div>
            <div class="stat-muted">Hex heatmap</div>
        </div>

        <div id="stats">
            <strong>Selected hex</strong><br>
            Click a hex cell to inspect its monthly and cumulative intersection counts.
        </div>
    </div>
    <div id="container"></div>

    <script>
        const {{
            DeckGL,
            GeoJsonLayer,
            TileLayer,
            BitmapLayer
        }} = deck;

const shapes = {json.dumps(all_shapes)};
const shapeHeatCells = {json.dumps(shape_heatmap_data.get("features", []))};
const eez = {json.dumps(eez_geojson)};
const hexes = {json.dumps(hex_features)};

        const monthNames = [
            "", "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ];

        const COLOR_RANGE = [
            [8, 48, 107],
            [8, 81, 156],
            [43, 140, 190],
            [123, 204, 196],
            [199, 233, 180],
            [254, 217, 118],
            [253, 141, 60],
            [227, 26, 28]
        ];

        function clamp(value, minValue, maxValue) {{
            return Math.max(minValue, Math.min(maxValue, value));
        }}

        function getColorFromCount(count, maxCount) {{
            if (!count || !maxCount) return [0, 0, 0, 0];
            const ratio = clamp(count / maxCount, 0, 1);
            const scaled = ratio * (COLOR_RANGE.length - 1);
            const index = Math.min(Math.floor(scaled), COLOR_RANGE.length - 2);
            const mix = scaled - index;
            const c1 = COLOR_RANGE[index];
            const c2 = COLOR_RANGE[index + 1];
            const r = Math.round(c1[0] + (c2[0] - c1[0]) * mix);
            const g = Math.round(c1[1] + (c2[1] - c1[1]) * mix);
            const b = Math.round(c1[2] + (c2[2] - c1[2]) * mix);
            return [r, g, b, 220];
        }}

        const initialViewState = {{
            longitude: 56.70,
            latitude: 25.33,
            zoom: 8.8,
            pitch: 0,
            bearing: 0
        }};

        let currentMonth = 1;
        let isPlaying = false;
        let interval = null;
        let selectedHexId = null;
        let heatMode = 'yearly';
        let previousHeatMode = 'yearly';

        const deckgl = new DeckGL({{
            container: 'container',
            initialViewState: initialViewState,
            controller: true,
            layers: []
        }});

        function monthCount(cell, month) {{
            const counts = cell.properties.monthly_counts || [];
            return counts[month - 1] || 0;
        }}

        function cumulativeCount(cell, month) {{
            const counts = cell.properties.monthly_counts || [];
            return counts.slice(0, month).reduce((sum, value) => sum + value, 0);
        }}

        function shapeHeatValue(cell) {{
            const props = cell.properties || {{}};
            if (heatMode === 'monthly') {{
                return (props.monthly_counts || [])[currentMonth - 1] || 0;
            }}
            if (heatMode === 'cumulative') {{
                return (props.monthly_counts || []).slice(0, currentMonth).reduce((sum, value) => sum + value, 0);
            }}
            return props.total_count || 0;
        }}

        function shapeHeatMax(features) {{
            let maxValue = 1;
            for (const cell of features) {{
                maxValue = Math.max(maxValue, shapeHeatValue(cell));
            }}
            return maxValue;
        }}

        function heatValue(cell) {{
            if (heatMode === 'monthly') return monthCount(cell, currentMonth);
            if (heatMode === 'cumulative') return cumulativeCount(cell, currentMonth);
            return cell.properties.total_count || 0;
        }}

        function heatMax() {{
            if (heatMode === 'monthly') return Math.max(...hexes.map(cell => monthCount(cell, currentMonth)), 1);
            if (heatMode === 'cumulative') return Math.max(...hexes.map(cell => cumulativeCount(cell, currentMonth)), 1);
            return Math.max(...hexes.map(cell => cell.properties.total_count || 0), 1);
        }}

        function updateStats(cell) {{
            const stats = document.getElementById('stats');
            if (!cell) {{
                stats.innerHTML = '<strong>Selected hex</strong><br><span class="stat-muted">Click a hex cell to inspect its monthly and cumulative intersection counts.</span>';
                return;
            }}

            const totalCount = cell.properties.total_count || 0;
            const currentCount = monthCount(cell, currentMonth);
            const cumulative = cumulativeCount(cell, currentMonth);
            const monthlyCounts = (cell.properties.monthly_counts || []).map((value, index) => {{
                return `<span class="stat-muted">${{monthNames[index + 1].slice(0, 3)}}:</span> ${{value}}`;
            }}).join('<br>');

            stats.innerHTML = `
                <strong>Selected hex #${{cell.properties.id}}</strong><br>
                Center: ${{cell.properties.center[0].toFixed(4)}}, ${{cell.properties.center[1].toFixed(4)}}<br>
                Total intersections: <strong>${{totalCount}}</strong><br>
                Cumulative to ${{monthNames[currentMonth]}}: <strong>${{cumulative}}</strong><br>
                Current month: <strong>${{currentCount}}</strong><br>
                <div style="margin-top:8px;" class="stat-muted">Monthly breakdown</div>
                <div style="margin-top:4px; line-height:1.4;">${{monthlyCounts}}</div>
            `;
        }}

        function updateLayers() {{
            const showNonEmptyOnly = document.getElementById('heatmap-cb').checked;
            const showHeatmap = document.getElementById('heatmap-cb').checked;
            const showShapes = document.getElementById('shapes-cb').checked;
            const showShapeHeatmap = document.getElementById('shape-heatmap-cb').checked;
            const selectedCell = hexes.find(cell => cell.properties.id === selectedHexId) || null;
            const maxValue = heatMax();
            const shapeData = heatMode === 'yearly'
                ? shapes
                : heatMode === 'cumulative'
                ? shapes.filter(f => f.properties.month <= currentMonth)
                : shapes.filter(f => f.properties.month === currentMonth);
            const heatCells = shapeHeatCells;
            const maxShapeValue = shapeHeatMax(heatCells);

            const layers = [];

            layers.push(new TileLayer({{
                id: 'base-tiles',
                data: 'https://basemaps.cartocdn.com/rastertiles/dark_all/{{z}}/{{x}}/{{y}}.png',
                minZoom: 0,
                maxZoom: 19,
                tileSize: 256,
                renderSubLayers: props => {{
                    const {{bbox: {{west, south, east, north}}}} = props.tile;
                    return new BitmapLayer(props, {{ data: null, image: props.data, bounds: [west, south, east, north] }});
                }}
            }}));

            layers.push(new GeoJsonLayer({{
                id: 'eez-outline',
                data: eez,
                filled: false,
                stroked: true,
                getLineColor: [45, 212, 191, 255],
                getLineWidth: 2
            }}));

            if (showHeatmap) {{
                layers.push(new GeoJsonLayer({{
                    id: 'hex-heatmap',
                    data: hexes,
                    pickable: true,
                    autoHighlight: true,
                    filled: true,
                    stroked: true,
                    lineWidthMinPixels: 1,
                    getLineColor: [255, 255, 255, 80],
                    getFillColor: cell => {{
                        const value = heatValue(cell);
                        const color = getColorFromCount(value, maxValue);
                        if (!value && showNonEmptyOnly) {{
                            return [0, 0, 0, 0];
                        }}
                        if (!value) {{
                            return [22, 28, 36, 24];
                        }}
                        const scale = clamp(value / maxValue, 0, 1);
                        const alpha = Math.round(70 + 150 * scale);
                        return [color[0], color[1], color[2], alpha];
                    }},
                    updateTriggers: {{
                        getFillColor: [currentMonth, heatMode, showNonEmptyOnly]
                    }},
                    onClick: info => {{
                        if (info.object) {{
                            selectedHexId = info.object.properties.id;
                            updateStats(info.object);
                            updateLayers();
                        }}
                    }}
                }}));
            }}

            if (showShapeHeatmap) {{
                layers.push(new GeoJsonLayer({{
                    id: 'shape-heatmap',
                    data: heatCells,
                    pickable: true,
                    filled: true,
                    stroked: false,
                    getFillColor: cell => {{
                        const value = shapeHeatValue(cell);
                        const color = getColorFromCount(value, maxShapeValue);
                        if (!value) {{
                            return [0, 0, 0, 0];
                        }}
                        const scale = clamp(value / maxShapeValue, 0, 1);
                        return [color[0], color[1], color[2], Math.round(70 + 150 * scale)];
                    }},
                    updateTriggers: {{ getFillColor: [currentMonth, heatMode, showShapeHeatmap] }}
                }}));
            }}

            if (showShapes) {{
                layers.push(new GeoJsonLayer({{
                    id: 'shapes',
                    data: shapeData,
                    filled: true,
                    stroked: true,
                    getFillColor: [210, 210, 210, 70],
                    getLineColor: [205, 205, 205, 220],
                    getLineWidth: 2,
                    updateTriggers: {{ data: [currentMonth, heatMode] }}
                }}));
            }}

            if (selectedCell) {{
                layers.push(new GeoJsonLayer({{
                    id: 'selected-hex',
                    data: selectedCell,
                    filled: false,
                    stroked: true,
                    getLineColor: [255, 255, 255, 255],
                    getLineWidth: 4
                }}));
            }}

            deckgl.setProps({{ layers: layers }});
            document.getElementById('month-name').innerText = monthNames[currentMonth] + ' 2025';
            document.getElementById('slider').value = currentMonth;
            if (selectedCell) {{
                updateStats(selectedCell);
            }}
        }}

        document.getElementById('slider').oninput = e => {{
            currentMonth = parseInt(e.target.value);
            updateLayers();
        }};

        document.querySelectorAll('input[name="heat-mode"]').forEach(el => {{
            el.onchange = () => {{
                heatMode = document.querySelector('input[name="heat-mode"]:checked').value;
                updateLayers();
            }};
        }});

        ['heatmap-cb', 'shapes-cb', 'shape-heatmap-cb'].forEach(id => {{
            const el = document.getElementById(id);
            if (el) el.onchange = () => updateLayers();
        }});

        document.getElementById('play-btn').onclick = () => {{
            isPlaying = !isPlaying;
            document.getElementById('play-btn').innerText = isPlaying ? 'Stop Animation' : 'Play Animation';
            if (isPlaying) {{
                previousHeatMode = heatMode;
                if (heatMode === 'yearly') {{
                    heatMode = 'monthly';
                    document.getElementById('mode-monthly').checked = true;
                }}
                interval = setInterval(() => {{
                    currentMonth = (currentMonth % 12) + 1;
                    selectedHexId = null;
                    updateStats(null);
                    updateLayers();
                }}, 800);
            }} else {{
                clearInterval(interval);
                heatMode = previousHeatMode;
                const modeInput = document.querySelector(`input[name="heat-mode"][value="${{heatMode}}"]`);
                if (modeInput) modeInput.checked = true;
                updateLayers();
            }}
        }};

        updateStats(null);
        updateLayers();
    </script>
</body>
</html>
"""

components.html(html_code, height=860)
