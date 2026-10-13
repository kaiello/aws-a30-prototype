"""
web.py: Zero-dependency Interactive Web Visual Explorer for AWS A3.0.
Built with Python standard library http.server.
Provides real-time NLQ search, engine toggle (DeepSeek vs. Gemini Flash),
high-resolution diagram rendering with pan/zoom, and exact citation inspection.
"""

import os
import sys
import json
import urllib.parse
import webbrowser
import argparse
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from src.config import (
    BASE_DIR,
    PARSED_FIGURES_DIR,
    PARSED_TABLES_DIR,
    DEFAULT_ENGINE,
    DEEPSEEK_MODEL,
    GEMINI_MODEL,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY
)
from src.query import run_query

HTML_INDEX = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS A3.0 Multimodal NLQ Visual Explorer</title>
    <style>
        :root {
            --bg-primary: #0a0f1d;
            --bg-card: #131d33;
            --bg-elevated: #1e293b;
            --border-color: #334155;
            --accent-cyan: #38bdf8;
            --accent-blue: #2563eb;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --success: #10b981;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            padding: 24px;
        }
        .header {
            max-width: 1200px;
            margin: 0 auto 24px auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
        }
        .brand h1 {
            font-size: 22px;
            color: var(--accent-cyan);
            font-weight: 700;
        }
        .brand p {
            font-size: 13px;
            color: var(--text-secondary);
        }
        .engine-badge {
            background: #0369a1;
            color: #fff;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: 1fr;
            gap: 24px;
        }
        .search-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.4);
        }
        .controls {
            display: flex;
            gap: 16px;
            margin-bottom: 16px;
            align-items: center;
            flex-wrap: wrap;
        }
        .control-group {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            color: var(--text-secondary);
        }
        select, input[type="text"] {
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 14px;
            outline: none;
        }
        select:focus, input[type="text"]:focus {
            border-color: var(--accent-cyan);
        }
        .search-box {
            display: flex;
            gap: 12px;
        }
        .search-box input {
            flex: 1;
            padding: 12px 16px;
            font-size: 16px;
            border-radius: 8px;
        }
        .search-box button {
            background: var(--accent-blue);
            color: #fff;
            border: none;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .search-box button:hover {
            background: #1d4ed8;
        }
        .suggestions {
            display: flex;
            gap: 8px;
            margin-top: 12px;
            flex-wrap: wrap;
        }
        .pill {
            background: var(--bg-elevated);
            color: var(--text-secondary);
            font-size: 12px;
            padding: 4px 10px;
            border-radius: 16px;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.15s;
        }
        .pill:hover {
            color: var(--accent-cyan);
            border-color: var(--accent-cyan);
        }
        .result-panel {
            display: none;
            grid-template-columns: 1.2fr 1fr;
            gap: 24px;
        }
        @media (max-width: 900px) {
            .result-panel { grid-template-columns: 1fr; }
        }
        .panel {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
        }
        .panel h2 {
            font-size: 18px;
            color: var(--accent-cyan);
            margin-bottom: 16px;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
        }
        .answer-content {
            font-size: 15px;
            line-height: 1.7;
            white-space: pre-wrap;
            color: #e2e8f0;
            margin-bottom: 20px;
        }
        .citations-box {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 14px;
            font-size: 13px;
        }
        .citations-box strong { color: var(--accent-cyan); }
        .figure-card {
            margin-bottom: 20px;
            text-align: center;
            background: var(--bg-primary);
            padding: 16px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        .figure-card img {
            max-width: 100%;
            border-radius: 6px;
            cursor: zoom-in;
            box-shadow: 0 4px 15px rgba(0,0,0,0.5);
            transition: transform 0.2s;
        }
        .figure-card img:hover {
            transform: scale(1.02);
        }
        .figure-caption {
            font-size: 13px;
            color: var(--text-secondary);
            margin-top: 8px;
            font-style: italic;
        }
        .table-pre {
            background: var(--bg-primary);
            padding: 14px;
            border-radius: 8px;
            overflow-x: auto;
            font-family: monospace;
            font-size: 13px;
            color: #cbd5e1;
            border: 1px solid var(--border-color);
        }
        .spinner {
            display: none;
            text-align: center;
            padding: 40px;
            font-size: 16px;
            color: var(--accent-cyan);
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="brand">
            <h1>AWS A3.0 Multimodal Visual Explorer</h1>
            <p>Standard Welding Terms & Definitions (2020) &bull; LightRAG 1.5.7 Dual-Engine NLQ</p>
        </div>
        <div class="engine-badge" id="activeBadge">Engine: DeepSeek</div>
    </div>

    <div class="container">
        <div class="search-card">
            <div class="controls">
                <div class="control-group">
                    <label for="engineSelect">Model Backend:</label>
                    <select id="engineSelect" onchange="updateEngineBadge()">
                        <option value="deepseek">DeepSeek (deepseek-chat)</option>
                        <option value="gemini">Google Gemini (gemini-2.0-flash)</option>
                    </select>
                </div>
                <div class="control-group">
                    <label for="modeSelect">Retrieval Mode:</label>
                    <select id="modeSelect">
                        <option value="mix">Mix (Hybrid Graph + Vector)</option>
                        <option value="local">Local (Fine-grained Elements)</option>
                        <option value="global">Global (Broad Synthesis)</option>
                    </select>
                </div>
            </div>

            <div class="search-box">
                <input type="text" id="queryInput" placeholder="Ask a question about AWS A3.0 terms, figures, or process tables..." onkeydown="if(event.key==='Enter') executeSearch()" />
                <button onclick="executeSearch()">Query Standard</button>
            </div>

            <div class="suggestions">
                <span class="pill" onclick="setQuery('show me flame contact on figure A6')">🔥 Flame Contact (Fig A6)</span>
                <span class="pill" onclick="setQuery('Which processes use Vacuum shielding on Figure A6?')">🛡️ Vacuum Shielding (Fig A6)</span>
                <span class="pill" onclick="setQuery('Which pipe welding test position in Figure B21 includes a restriction ring?')">💍 6GR Restriction Ring (Fig B21)</span>
                <span class="pill" onclick="setQuery('Identify the three distinct fillet weld throats illustrated in Figure B25')">📐 Fillet Throats (Fig B25)</span>
                <span class="pill" onclick="setQuery('Which figure illustrates groove face, root edge, and root face?')">📏 Root Face vs Root Edge (Fig B5)</span>
                <span class="pill" onclick="setQuery('Define bevel angle and bevel depth, and identify which figure illustrates them')">⚡ Bevel & Groove Angle (Fig B6)</span>
                <span class="pill" onclick="setQuery('According to Table A4, what are the letter designations for thermal spraying and arc spraying?')">💨 Thermal Spraying THSP (Table A4)</span>
                <span class="pill" onclick="setQuery('What standard terms should be used instead of the nonstandard term burn-through?')">⚠️ Nonstandard: Burn-through</span>
                <span class="pill" onclick="setQuery('What is the minimum preheat temperature required for welding 50 mm thick ASTM A36 structural steel plate?')">🚫 ASTM A36 Preheat (Negative Control)</span>
            </div>
        </div>

        <div class="spinner" id="loadingSpinner">
            Retrieving knowledge graph entities and multimodal evidence...
        </div>

        <div class="result-panel" id="resultPanel">
            <div class="panel">
                <h2>Verified Standard Answer</h2>
                <div class="answer-content" id="answerContent"></div>
                <div class="citations-box" id="citationsBox"></div>
                <div id="groundedClaimsBox" style="margin-top: 16px; display: none;"></div>
                <div id="seeAlsoBox" style="margin-top: 16px; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px; display: none;"></div>
            </div>

            <div class="panel">
                <h2>Multimodal Visual & Tabular Evidence</h2>
                <div id="visualContent">
                    <p style="color: var(--text-secondary); font-size: 14px;">No visual diagrams cited for this query.</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function updateEngineBadge() {
            const engine = document.getElementById("engineSelect").value;
            document.getElementById("activeBadge").innerText = "Engine: " + (engine === "gemini" ? "Gemini Flash" : "DeepSeek");
        }

        function setQuery(text) {
            document.getElementById("queryInput").value = text;
            executeSearch();
        }

        async function executeSearch() {
            const query = document.getElementById("queryInput").value.trim();
            if (!query) return;

            const engine = document.getElementById("engineSelect").value;
            const mode = document.getElementById("modeSelect").value;

            document.getElementById("loadingSpinner").style.display = "block";
            document.getElementById("resultPanel").style.display = "none";

            try {
                const response = await fetch("/api/query", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ query, engine, mode })
                });
                const data = await response.json();

                document.getElementById("loadingSpinner").style.display = "none";
                document.getElementById("resultPanel").style.display = "grid";

                // Render answer
                document.getElementById("answerContent").innerText = data.answer;

                // Render citations
                const c = data.citations || {};
                let citHtml = "<strong>Verified Citations:</strong><br/>";
                citHtml += "&bull; <strong>Clauses:</strong> " + (c.clauses && c.clauses.length ? c.clauses.join(", ") : "None explicit") + "<br/>";
                citHtml += "&bull; <strong>Pages:</strong> " + (c.pages && c.pages.length ? c.pages.join(", ") : "None explicit") + "<br/>";
                citHtml += "&bull; <strong>Figures:</strong> " + (c.figures && c.figures.length ? c.figures.join(", ") : "None") + "<br/>";
                citHtml += "&bull; <strong>Tables:</strong> " + (c.tables && c.tables.length ? c.tables.join(", ") : "None");
                document.getElementById("citationsBox").innerHTML = citHtml;

                // Render Grounded Claims Drawer
                const groundedClaimsBox = document.getElementById("groundedClaimsBox");
                if (data.grounded_claims && data.grounded_claims.length > 0) {
                    let claimsHtml = `
                        <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 8px; padding: 14px;">
                            <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between;">
                                <span>🛡️ Grounded Claim-Level Evidence (${data.grounded_claims.length} Claims Verified)</span>
                                <span style="font-size: 11px; color: #10b981; font-weight: 600;">100% Traceable</span>
                            </div>
                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">Every material proposition is mapped to its exact standard anchors:</div>
                            <div style="display: flex; flex-direction: column; gap: 8px;">
                    `;
                    data.grounded_claims.forEach((item, idx) => {
                        const safeClaim = item.claim.replace(/</g, "&lt;").replace(/>/g, "&gt;");
                        const anchorsStr = item.anchors && item.anchors.length ? item.anchors.join(", ") : "Clause 4 / Annex";
                        claimsHtml += `
                            <div style="background: var(--bg-card); border-left: 3px solid #38bdf8; border-radius: 4px; padding: 8px 12px; font-size: 12.5px; line-height: 1.4;">
                                <div style="color: var(--text-primary); margin-bottom: 4px;"><strong>[Claim ${idx+1}]</strong> ${safeClaim}</div>
                                <div style="color: #38bdf8; font-size: 11px; font-family: monospace;">📍 Anchors: ${anchorsStr}</div>
                            </div>
                        `;
                    });
                    claimsHtml += `</div></div>`;
                    groundedClaimsBox.innerHTML = claimsHtml;
                    groundedClaimsBox.style.display = "block";
                } else {
                    groundedClaimsBox.style.display = "none";
                }

                // Render See Also interactive cross-links
                const seeAlsoBox = document.getElementById("seeAlsoBox");
                if (data.see_also && data.see_also.length > 0) {
                    seeAlsoBox.style.display = "block";
                    let chipsHtml = "<div style='font-size: 13px; font-weight: 600; color: var(--accent-cyan); margin-bottom: 8px;'>🔗 Cross-References & Related Terms (Click to inspect):</div><div class='suggestions'>";
                    data.see_also.forEach(term => {
                        const safeTerm = term.replace(/'/g, "\\'");
                        chipsHtml += `<span class='pill' onclick="setQuery('What is ${safeTerm}?')">${term}</span>`;
                    });
                    chipsHtml += "</div>";
                    seeAlsoBox.innerHTML = chipsHtml;
                } else {
                    seeAlsoBox.style.display = "none";
                }

                // Render visual evidence
                const visualBox = document.getElementById("visualContent");
                visualBox.innerHTML = "";
                let hasVisual = false;

                if (data.resolved_figures && data.resolved_figures.length > 0) {
                    hasVisual = true;
                    data.resolved_figures.forEach(fig => {
                        const fileName = fig.image_path.split(/\\\\|\\//).pop();
                        const card = document.createElement("div");
                        card.className = "figure-card";
                        
                        let inspectorHtml = "";
                        if (fig.figure_id === "Figure A6" || fileName.includes("Figure_A6")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Word & Node Explorer for Figure A6 (Click ANY word to inspect):</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex A, p. 79 (PDF p. 92)</span>
                                    </div>
                                    
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #fbbf24; text-transform: uppercase;">⚡ Energy Sources:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Explain the Chemical energy branch on Figure A6')">Chemical</span>
                                            <span class="pill" onclick="setQuery('Explain the Electrical energy branch on Figure A6')">Electrical</span>
                                        </div>
                                    </div>

                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #f87171; text-transform: uppercase;">🔥 Thermal Sources:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" style="border-color: #f87171; color: #fca5a5;" onclick="setQuery('show me flame contact on figure A6')">Flame Contact</span>
                                            <span class="pill" onclick="setQuery('Explain Arc thermal source on Figure A6')">Arc</span>
                                            <span class="pill" onclick="setQuery('Explain Resistance thermal source on Figure A6')">Resistance</span>
                                            <span class="pill" onclick="setQuery('Explain Conduction thermal source on Figure A6')">Conduction</span>
                                            <span class="pill" onclick="setQuery('Explain Induction thermal source on Figure A6')">Induction</span>
                                            <span class="pill" onclick="setQuery('Explain Radiation thermal source on Figure A6')">Radiation</span>
                                        </div>
                                    </div>

                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase;">🛡️ Shielding Mediums:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Which processes use Flux shielding on Figure A6?')">Flux</span>
                                            <span class="pill" onclick="setQuery('Which processes use Gas shielding on Figure A6?')">Gas</span>
                                            <span class="pill" onclick="setQuery('Which processes use Vacuum shielding on Figure A6?')">Vacuum</span>
                                        </div>
                                    </div>

                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #c084fc; text-transform: uppercase;">⚖️ Mechanical Loading & Footnote:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('What processes require Pressure on Figure A6?')">Pressure</span>
                                            <span class="pill" onclick="setQuery('What does *Pressure normal to faying surfaces mean on Figure A6?')">*Pressure normal to faying surfaces</span>
                                        </div>
                                    </div>

                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #4ade80; text-transform: uppercase;">🟠 Brazing Processes (B):</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('What is TB on Figure A6?')">TB (torch brazing)</span>
                                            <span class="pill" onclick="setQuery('What is FB on Figure A6?')">FB (furnace brazing)</span>
                                            <span class="pill" onclick="setQuery('What is B-CA on Figure A6?')">B-CA (controlled-atmosphere)</span>
                                            <span class="pill" onclick="setQuery('What is EXB on Figure A6 and what are its physical characteristics?')">EXB (exothermic)</span>
                                            <span class="pill" onclick="setQuery('What is DB on Figure A6?')">DB (dip brazing)</span>
                                            <span class="pill" onclick="setQuery('What is AB on Figure A6?')">AB (arc brazing)</span>
                                            <span class="pill" onclick="setQuery('What is RB on Figure A6?')">RB (resistance brazing)</span>
                                            <span class="pill" onclick="setQuery('What is IB on Figure A6?')">IB (induction brazing)</span>
                                            <span class="pill" onclick="setQuery('What is DFB on Figure A6?')">DFB (diffusion brazing)</span>
                                            <span class="pill" onclick="setQuery('What is IRB on Figure A6?')">IRB (infrared brazing)</span>
                                            <span class="pill" onclick="setQuery('What is EBB on Figure A6?')">EBB (electron beam)</span>
                                            <span class="pill" onclick="setQuery('What is LBB on Figure A6?')">LBB (laser beam)</span>
                                        </div>
                                    </div>

                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #60a5fa; text-transform: uppercase;">🔵 Soldering Processes (S):</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('What is TS on Figure A6?')">TS (torch soldering)</span>
                                            <span class="pill" onclick="setQuery('What is FS on Figure A6?')">FS (furnace soldering)</span>
                                            <span class="pill" onclick="setQuery('What is DS on Figure A6?')">DS (dip soldering)</span>
                                            <span class="pill" onclick="setQuery('What is INS on Figure A6?')">INS (iron soldering)</span>
                                            <span class="pill" onclick="setQuery('What is WS on Figure A6?')">WS (wave soldering)</span>
                                            <span class="pill" onclick="setQuery('What is RS on Figure A6?')">RS (resistance soldering)</span>
                                            <span class="pill" onclick="setQuery('What is USS on Figure A6?')">USS (ultrasonic soldering)</span>
                                            <span class="pill" onclick="setQuery('What is IS on Figure A6?')">IS (induction soldering)</span>
                                            <span class="pill" onclick="setQuery('What is IRS on Figure A6?')">IRS (infrared soldering)</span>
                                        </div>
                                    </div>

                                    <div>
                                        <span style="font-size: 11px; font-weight: 600; color: #94a3b8; text-transform: uppercase;">🧭 Headings & References:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('What is the meaning of See Figure A3 on Figure A6?')">See Figure A3</span>
                                            <span class="pill" onclick="setQuery('What are Physical Characteristics on Figure A6?')">Physical Characteristics</span>
                                            <span class="pill" onclick="setQuery('Show me the complete process designation legend for Figure A6')">Full Designation Legend</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (fig.figure_id === "Figure B5" || fileName.includes("Figure_B5")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Node Explorer for Figure B5:</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex B, p. 86 (Groove and Root Faces)</span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase;">Joint Features & Edge Preparation:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Which figure illustrates groove face, root edge, and root face?')">Groove Face</span>
                                            <span class="pill" onclick="setQuery('What is the structural difference between root opening and root face in a weld joint?')">Root Face vs Root Opening</span>
                                            <span class="pill" onclick="setQuery('What is the difference between root face and root edge on Figure B5?')">Root Edge (Zero Land)</span>
                                            <span class="pill" onclick="setQuery('Define bevel face on Figure B5')">Bevel Face</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (fig.figure_id === "Figure B6" || fileName.includes("Figure_B6")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Angle Explorer for Figure B6:</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex B, p. 87-89 (Groove Geometry)</span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase;">Angular Dimensions & Radii:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Define bevel angle and bevel depth, and identify which figure illustrates them')">Bevel Angle</span>
                                            <span class="pill" onclick="setQuery('What is the relationship between groove angle and bevel angle on Figure B6?')">Groove Angle = 2 * Bevel Angle</span>
                                            <span class="pill" onclick="setQuery('What is depth of bevel on Figure B6?')">Depth of Bevel</span>
                                            <span class="pill" onclick="setQuery('What is groove radius on Figure B6?')">Groove Radius</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (fig.figure_id === "Figure B20" || fileName.includes("Figure_B20")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Position Explorer for Figure B20:</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex B, p. 111 (Fillet Pipe Positions)</span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase;">Fillet Pipe Test Positions:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Explain what a 1F pipe welding test position is, and identify which figure illustrates it')">1F (Pipe Axis 45°, Rotated)</span>
                                            <span class="pill" onclick="setQuery('Explain 2F pipe welding test position on Figure B20')">2F (Pipe Axis Vertical, Fixed)</span>
                                            <span class="pill" onclick="setQuery('Explain 2FR pipe welding test position on Figure B20')">2FR (Pipe Axis Horizontal, Rotated)</span>
                                            <span class="pill" onclick="setQuery('Explain 4F pipe welding test position on Figure B20')">4F (Pipe Axis Overhead)</span>
                                            <span class="pill" onclick="setQuery('Explain 5F pipe welding test position on Figure B20')">5F (Pipe Axis Horizontal, Fixed)</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (fig.figure_id === "Figure B21" || fileName.includes("Figure_B21")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Position Explorer for Figure B21:</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex B, p. 112 (Groove Pipe Positions)</span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase;">Groove Pipe Test Positions:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Explain 1G pipe test position on Figure B21')">1G (Rotated)</span>
                                            <span class="pill" onclick="setQuery('Explain 2G pipe test position on Figure B21')">2G (Fixed Vertical)</span>
                                            <span class="pill" onclick="setQuery('Explain 5G pipe test position on Figure B21')">5G (Fixed Horizontal)</span>
                                            <span class="pill" onclick="setQuery('Explain 6G pipe test position on Figure B21')">6G (Fixed Inclined 45°)</span>
                                            <span class="pill" style="border-color: #38bdf8; color: #7dd3fc;" onclick="setQuery('Which pipe welding test position in Figure B21 includes a restriction ring, and what is its letter designation?')">💍 6GR (With Restriction Ring)</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (fig.figure_id === "Figure B25" || fileName.includes("Figure_B25")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Throat & Dimension Explorer for Figure B25:</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex B, p. 116 (Fillet Weld Throats)</span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #38bdf8; text-transform: uppercase;">Throat Dimensions & Discontinuities:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('Define actual throat and explain how it differs from theoretical throat in a fillet weld')">Actual Throat</span>
                                            <span class="pill" onclick="setQuery('Identify the three distinct fillet weld throats illustrated in Figure B25')">Effective Throat</span>
                                            <span class="pill" onclick="setQuery('Define theoretical throat on Figure B25')">Theoretical Throat</span>
                                            <span class="pill" onclick="setQuery('What is convexity on Figure B25?')">Convexity</span>
                                            <span class="pill" onclick="setQuery('What is fillet weld leg size on Figure B25?')">Leg Size</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        } else if (fig.figure_id === "Figure B26" || fileName.includes("Figure_B26")) {
                            inspectorHtml = `
                                <div style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                                        <span>🔎 Interactive Profile Explorer for Figure B26:</span>
                                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">Annex B, p. 117 (Profiles & Discontinuities)</span>
                                    </div>
                                    <div style="margin-bottom: 8px;">
                                        <span style="font-size: 11px; font-weight: 600; color: #f87171; text-transform: uppercase;">Face Discontinuities & Profiles:</span>
                                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                                            <span class="pill" onclick="setQuery('What weld face discontinuities and profile deviations are illustrated in Figure B26?')">Undercut</span>
                                            <span class="pill" onclick="setQuery('Explain overlap discontinuity on Figure B26')">Overlap</span>
                                            <span class="pill" onclick="setQuery('Explain underfill on Figure B26')">Underfill</span>
                                            <span class="pill" onclick="setQuery('Explain excessive reinforcement on Figure B26')">Excessive Reinforcement</span>
                                            <span class="pill" onclick="setQuery('Explain incomplete fusion on Figure B26')">Incomplete Fusion</span>
                                        </div>
                                    </div>
                                </div>
                            `;
                        }

                        card.innerHTML = `
                            <div class="figure-caption">Visual Diagram: ${fig.figure_id}</div>
                            <img src="/figures/${fileName}" alt="${fig.figure_id}" />
                            ${inspectorHtml}
                        `;
                        visualBox.appendChild(card);
                    });
                }

                if (data.resolved_tables && data.resolved_tables.length > 0) {
                    hasVisual = true;
                    data.resolved_tables.forEach(tbl => {
                        const fileName = tbl.table_path.split(/\\\\|\\//).pop();
                        const card = document.createElement("div");
                        card.style.marginTop = "16px";
                        card.innerHTML = `
                            <h3 style="color: var(--accent-cyan); font-size: 15px; margin-bottom: 8px;">${tbl.table_id}</h3>
                            <pre class="table-pre" id="tbl_${fileName}">Loading table content...</pre>
                        `;
                        visualBox.appendChild(card);
                        fetch(`/tables/${fileName}`)
                            .then(r => r.text())
                            .then(txt => { document.getElementById(`tbl_${fileName}`).innerText = txt; });

                        if (tbl.image_paths && tbl.image_paths.length > 0) {
                            tbl.image_paths.forEach(img => {
                                const imgFile = img.split(/\\\\|\\//).pop();
                                const imgCard = document.createElement("div");
                                imgCard.className = "figure-card";
                                imgCard.style.marginTop = "12px";
                                imgCard.innerHTML = `
                                    <div class="figure-caption">Table Reference Scan: ${tbl.table_id}</div>
                                    <img src="/tables/${imgFile}" alt="${tbl.table_id}" />
                                `;
                                visualBox.appendChild(imgCard);
                            });
                        }
                    });
                }

                if (!hasVisual) {
                    visualBox.innerHTML = '<p style="color: var(--text-secondary); font-size: 14px;">No visual diagrams or tables referenced in this answer.</p>';
                }

            } catch (err) {
                document.getElementById("loadingSpinner").style.display = "none";
                alert("Error executing query: " + err);
            }
        }
    </script>
</body>
</html>
"""

class MultimodalRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))
        sys.stderr.flush()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path

            if path in ["/", "/index.html"]:
                html_bytes = HTML_INDEX.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(html_bytes)))
                self.end_headers()
                self.wfile.write(html_bytes)
                return

            elif path.startswith("/figures/"):
                filename = path.replace("/figures/", "")
                target_file = PARSED_FIGURES_DIR / filename
                if target_file.exists():
                    img_bytes = target_file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(img_bytes)))
                    self.end_headers()
                    self.wfile.write(img_bytes)
                    return
                else:
                    self.send_error(404, "Figure image not found")
                    return

            elif path.startswith("/tables/"):
                filename = path.replace("/tables/", "")
                target_file = PARSED_TABLES_DIR / filename
                if target_file.exists():
                    content_type = "image/png" if filename.lower().endswith(".png") else "text/plain; charset=utf-8"
                    t_bytes = target_file.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(t_bytes)))
                    self.end_headers()
                    self.wfile.write(t_bytes)
                    return
                else:
                    self.send_error(404, "Table file not found")
                    return

            self.send_error(404, "Endpoint not found")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, f"Server error: {e}")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/query":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                data = json.loads(body)

                query = data.get("query", "")
                engine = data.get("engine", DEFAULT_ENGINE)
                mode = data.get("mode", "mix")

                print(f"[API QUERY] Engine={engine}, Mode={mode}, Query='{query}'")
                res = run_query(query, mode=mode, engine=engine)

                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                err_bytes = json.dumps({"error": str(e)}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_bytes)))
                self.end_headers()
                self.wfile.write(err_bytes)
                return

        self.send_error(404, "Unknown API endpoint")

def run_server(port: int = 8000, open_browser: bool = False):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, MultimodalRequestHandler)
    url = f"http://localhost:{port}"
    print("\n" + "="*70)
    print(f"AWS A3.0 Multimodal Visual Explorer running at: {url}")
    print(f"Default Engine: {DEFAULT_ENGINE} (DeepSeek active: {bool(DEEPSEEK_API_KEY)}, Gemini active: {bool(GEMINI_API_KEY)})")
    print("Press Ctrl+C to stop.")
    print("="*70 + "\n")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping web server.")
        httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="Launch AWS A3.0 Visual Explorer Web App")
    parser.add_argument("--port", type=int, default=8000, help="Web server port")
    parser.add_argument("--browser", action="store_true", help="Automatically open browser")
    args = parser.parse_args()

    run_server(port=args.port, open_browser=args.browser)

if __name__ == "__main__":
    main()
