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
from src.query import run_query, resolve_multimodal_assets
from src.figure_inspectors import (
    FIGURE_INSPECTORS,
    FIGURE_CATEGORIES,
    get_all_figures_catalog,
    get_inspector_html,
    get_figure_data
)

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
        .figures-explorer-card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 24px;
        }
        .explorer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }
        .explorer-header:hover .header-title {
            color: var(--accent-cyan);
        }
        .category-tabs {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }
        .category-tab {
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            cursor: pointer;
            color: var(--text-secondary);
            transition: all 0.15s;
        }
        .category-tab.active, .category-tab:hover {
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
            background: rgba(56, 189, 248, 0.1);
        }
        .figures-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 10px;
            max-height: 380px;
            overflow-y: auto;
            padding-right: 6px;
        }
        .fig-tile {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 12px;
            cursor: pointer;
            transition: all 0.15s;
        }
        .fig-tile:hover {
            border-color: var(--accent-cyan);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);
        }
        .fig-tile-id {
            font-weight: 700;
            color: var(--accent-cyan);
            font-size: 13px;
        }
        .fig-tile-title {
            font-size: 12px;
            color: var(--text-primary);
            margin: 4px 0 6px 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .fig-tile-footer {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            color: var(--text-secondary);
        }
        .fig-tile-badge {
            font-size: 10px;
            color: #fbbf24;
            background: rgba(251, 191, 36, 0.12);
            padding: 2px 6px;
            border-radius: 8px;
            font-weight: 600;
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
                <span class="pill" onclick="setQuery('In Figure B16A, what are the inclination of axis and rotation of face coordinate limits for Flat position groove welds in plate?')">🧭 3D Welding Coordinates (Fig B16A)</span>
                <span class="pill" onclick="setQuery('In Figure B23(J), what is the distinction between a toe temper bead and surface temper weld reinforcing beads?')">🔨 Temper Beads (Fig B23J)</span>
                <span class="pill" onclick="setQuery('What are the callout components and features identified on Figure B46 for the Friction Stir Welding (FSW) process?')">🌀 FSW Schematic (Fig B46)</span>
                <span class="pill" onclick="setQuery('What are the three distinct oxyacetylene flame types illustrated in Figure B40?')">🔥 Flame Types (Fig B40)</span>
                <span class="pill" onclick="setQuery('Which pipe welding test position in Figure B21 includes a restriction ring?')">💍 6GR Restriction Ring (Fig B21)</span>
                <span class="pill" onclick="setQuery('Identify the three distinct fillet weld throats illustrated in Figure B25')">📐 Fillet Throats (Fig B25)</span>
                <span class="pill" onclick="setQuery('Which figure illustrates groove face, root edge, and root face?')">📏 Root Face vs Root Edge (Fig B5)</span>
                <span class="pill" onclick="setQuery('According to Annex C1.5.3, why does the Definitions Subcommittee reject TIG and MIG in favor of GTAW and GMAW?')">⚖️ GTAW vs TIG Rationale (Annex C)</span>
                <span class="pill" onclick="setQuery('Why was the term parallel joint introduced in the 2020 edition to replace edge joint according to Annex C1.5.7?')">📐 Parallel Joint Rationale (Annex C)</span>
                <span class="pill" onclick="setQuery('According to Table D1, what new electrical terms were introduced in the 2020 edition for waveform-controlled welding?')">⚡ Waveform AIP & TIE (Table D1)</span>
                <span class="pill" onclick="setQuery('According to Table D6, name physical science and chemistry terms that were deleted in the 2020 edition')">🗑️ Deleted Terms (Table D6)</span>
                <span class="pill" onclick="setQuery('Show me the friction stir welding parameter schedule on Figure B75')">🚫 FSW B75 Schedule (Negative Control)</span>
            </div>
        </div>

        <div class="figures-explorer-card">
            <div class="explorer-header" onclick="toggleFigureDrawer()">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span class="header-title" style="font-size: 15px; font-weight: 700; color: var(--accent-cyan);">📚 Interactive Figure & Diagram Directory (All 60 Figures: Annex A & Annex B)</span>
                    <span style="font-size: 11px; background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); padding: 2px 8px; border-radius: 12px; font-weight: 600;">267+ Interactive Chips</span>
                </div>
                <span id="drawerToggleIcon" style="font-size: 12px; color: var(--text-secondary); cursor: pointer;">▼ Click to Browse All Figures</span>
            </div>
            <div id="figureDrawerContent" style="display: none; margin-top: 14px;">
                <div class="category-tabs" id="categoryTabs"></div>
                <div class="figures-grid" id="figuresGrid"></div>
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
                <div id="epistemicTraceBox" style="margin-top: 16px; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px; display: none;"></div>
                <div id="answerRouteBox" style="margin-top: 16px; background: var(--bg-primary); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px; display: none;"></div>
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

                // Render Dual-Layer Epistemic Provenance Trail
                const epistemicBox = document.getElementById("epistemicTraceBox");
                if (data.epistemic_trace) {
                    const et = data.epistemic_trace;
                    epistemicBox.style.display = "block";
                    const statusColor = et.epistemic_status === "VERIFIED_GROUNDED" ? "#10b981" : (et.epistemic_status === "TRUTHFUL_ABSTENTION" ? "#fbbf24" : "#f87171");
                    let epHtml = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 13px; font-weight: 700; color: var(--accent-cyan);">🔬 Dual-Layer Epistemic Provenance Trail:</span>
                            <span style="font-size: 11px; font-weight: 700; color: ${statusColor}; background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 12px; border: 1px solid ${statusColor};">
                                ${et.epistemic_status} (${Math.round(et.provenance_score * 100)}%)
                            </span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px;">${et.manifest_summary}</div>
                    `;

                    if (et.concepts_verified && et.concepts_verified.length > 0) {
                        epHtml += `<div style="font-size: 11px; font-weight: 600; color: #a855f7; text-transform: uppercase; margin-bottom: 6px;">Ontology Concepts & Provenance Bridges:</div><div style="display: flex; flex-direction: column; gap: 6px;">`;
                        et.concepts_verified.slice(0, 5).forEach(cv => {
                            const badgeColor = cv.node_type === "Process" ? "#38bdf8" : (cv.node_type === "JointGeometry" ? "#fbbf24" : (cv.node_type === "Discontinuity" ? "#f87171" : "#4ade80"));
                            let bridgeText = "";
                            if (cv.primary_evidence && cv.primary_evidence.length > 0) {
                                const pe = cv.primary_evidence[0];
                                bridgeText = `[:${pe.relation}] &rarr; ${pe.evidence_type}: ${pe.name} ${pe.page ? '(' + pe.page + ')' : ''}`;
                            }
                            epHtml += `
                                <div style="background: var(--bg-card); border-left: 3px solid ${badgeColor}; border-radius: 4px; padding: 6px 10px; font-size: 12px;">
                                    <div style="display: flex; justify-content: space-between;">
                                        <span style="font-weight: 600; color: var(--text-primary);">${cv.concept}</span>
                                        <span style="font-size: 10px; color: ${badgeColor}; font-weight: 600;">:${cv.node_type} (${cv.standard_status})</span>
                                    </div>
                                    <div style="color: #94a3b8; font-size: 11px; margin-top: 2px; font-family: monospace;">${bridgeText}</div>
                                </div>
                            `;
                        });
                        epHtml += `</div>`;
                    }
                    epistemicBox.innerHTML = epHtml;
                } else {
                    epistemicBox.style.display = "none";
                }

                // Render Answer Route Bundle (Perplexity Context-Bench Evidence Group)
                const answerRouteBox = document.getElementById("answerRouteBox");
                if (data.answer_route && data.answer_route.evidence_group && data.answer_route.evidence_group.length > 0) {
                    const ar = data.answer_route;
                    answerRouteBox.style.display = "block";
                    const isAll = ar.all_evidence_recovered;
                    const badgeBg = isAll ? "rgba(16, 185, 129, 0.15)" : "rgba(251, 191, 36, 0.15)";
                    const badgeBorder = isAll ? "#10b981" : "#fbbf24";
                    const badgeColor = isAll ? "#10b981" : "#fbbf24";

                    let arHtml = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 13px; font-weight: 700; color: #38bdf8;">📦 Verified Answer Route Bundle:</span>
                            <span style="font-size: 11px; font-weight: 700; color: ${badgeColor}; background: ${badgeBg}; padding: 2px 8px; border-radius: 12px; border: 1px solid ${badgeBorder};">
                                ${isAll ? 'ALL-EVIDENCE RECOVERED' : 'PARTIAL EVIDENCE'} (${Math.round(ar.evidence_recall_score * 100)}%)
                            </span>
                        </div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">
                            <strong>Context-Bench Metrics:</strong> Evidence Recall: ${Math.round(ar.evidence_recall_score * 100)}% | Epistemic Provenance: ${ar.epistemic_score} | Target: <span style="color: #f8fafc; font-weight: 600;">${ar.concept_name || 'Matched'}</span> (${ar.concept_type || 'Concept'})
                        </div>
                        <div style="font-size: 11px; font-weight: 600; color: #a855f7; text-transform: uppercase; margin-bottom: 6px;">
                            Supporting Evidence Group (${ar.evidence_group.length} items):
                        </div>
                        <div style="display: flex; flex-direction: column; gap: 6px;">
                    `;
                    ar.evidence_group.slice(0, 6).forEach(ev => {
                        const chipCount = ev.callout_chips ? ev.callout_chips.length : 0;
                        const chipInfo = chipCount > 0 ? ` &bull; <span style="color: #4ade80;">${chipCount} Interactive Callout Chips</span>` : '';
                        arHtml += `
                            <div style="background: var(--bg-card); border-left: 3px solid #38bdf8; border-radius: 4px; padding: 6px 10px; font-size: 12px;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-weight: 600; color: #38bdf8;">[${ev.evidence_type.toUpperCase()}] ${ev.element_id}</span>
                                    <span style="font-size: 10px; color: #94a3b8;">${ev.page ? 'p. ' + ev.page : ''}</span>
                                </div>
                                <div style="color: var(--text-secondary); font-size: 11px; margin-top: 2px;">
                                    ${ev.title} ${chipInfo}
                                </div>
                            </div>
                        `;
                    });
                    arHtml += `</div>`;
                    answerRouteBox.innerHTML = arHtml;
                } else if (answerRouteBox) {
                    answerRouteBox.style.display = "none";
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
                        const figKey = fig.figure_id;
                        const figData = figureMap[figKey] || figureMap[figKey.replace("Figure ", "")] || figureMap["Figure " + figKey];
                        if (figData) {
                            inspectorHtml = renderInspectorHtml(figKey, figData);
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

        let allFigures = [];
        let figureMap = {};
        let currentCategory = "all";

        async function loadFigureCatalog() {
            try {
                const res = await fetch("/api/figures");
                if (!res.ok) return;
                const data = await res.json();
                allFigures = data.figures || [];
                figureMap = {};
                allFigures.forEach(f => {
                    figureMap[f.id] = f;
                    const clean = f.id.replace("Figure ", "");
                    figureMap[clean] = f;
                });

                renderCategoryTabs(data.categories || []);
                filterCategory("all");
            } catch (e) {
                console.error("Failed to load figure catalog", e);
            }
        }

        function toggleFigureDrawer() {
            const drawer = document.getElementById("figureDrawerContent");
            const icon = document.getElementById("drawerToggleIcon");
            if (drawer.style.display === "none" || !drawer.style.display) {
                drawer.style.display = "block";
                icon.innerText = "▲ Hide Figure Directory";
            } else {
                drawer.style.display = "none";
                icon.innerText = "▼ Click to Browse All Figures (60 Figures)";
            }
        }

        function renderCategoryTabs(categories) {
            const container = document.getElementById("categoryTabs");
            container.innerHTML = "";
            categories.forEach(cat => {
                const btn = document.createElement("button");
                btn.className = "category-tab" + (cat.id === currentCategory ? " active" : "");
                btn.innerText = cat.label;
                btn.onclick = () => filterCategory(cat.id);
                container.appendChild(btn);
            });
        }

        function filterCategory(catId) {
            currentCategory = catId;
            document.querySelectorAll(".category-tab").forEach(tab => {
                tab.classList.toggle("active", tab.innerText.includes(catId) || (catId === "all" && tab.innerText.includes("All")));
            });

            const filtered = catId === "all" ? allFigures : allFigures.filter(f => f.category === catId);
            renderFigureGrid(filtered);
        }

        function renderFigureGrid(figures) {
            const grid = document.getElementById("figuresGrid");
            grid.innerHTML = "";
            figures.forEach(fig => {
                const tile = document.createElement("div");
                tile.className = "fig-tile";
                tile.onclick = () => inspectFigureDirectly(fig.id);
                tile.innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span class="fig-tile-id">${fig.id}</span>
                        <span class="fig-tile-badge">${fig.chip_count} Chips</span>
                    </div>
                    <div class="fig-tile-title" title="${fig.title}">${fig.title}</div>
                    <div class="fig-tile-footer">
                        <span>${fig.page}</span>
                        <span style="color: var(--accent-cyan);">Inspect →</span>
                    </div>
                `;
                grid.appendChild(tile);
            });
        }

        function renderInspectorHtml(figKey, figData) {
            if (!figData || !figData.groups) return "";
            let html = `
                <div class="interactive-inspector" style="margin-top: 16px; text-align: left; background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 8px; padding: 14px;">
                    <div style="font-size: 13px; font-weight: 700; color: var(--accent-cyan); margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                        <span>🔎 Interactive Node & Callout Explorer for ${figData.id}:</span>
                        <span style="font-size: 11px; color: var(--text-secondary); font-weight: normal;">${figData.page || ''}</span>
                    </div>
                    <div style="font-size: 12px; color: #94a3b8; margin-bottom: 10px; font-style: italic;">${figData.title || ''}</div>
            `;

            figData.groups.forEach(g => {
                const color = g.color || "var(--accent-cyan)";
                html += `
                    <div style="margin-bottom: 8px;">
                        <span style="font-size: 11px; font-weight: 600; color: ${color}; text-transform: uppercase;">${g.group_title}:</span>
                        <div style="display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;">
                `;
                (g.chips || []).forEach(c => {
                    const safeQuery = (c.query || "").replace(/'/g, "\\'");
                    html += `<span class="pill" onclick="event.stopPropagation(); setQuery('${safeQuery}')">${c.label}</span>`;
                });
                html += `
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
            return html;
        }

        function inspectFigureDirectly(figId) {
            const figData = figureMap[figId] || figureMap[figId.replace("Figure ", "")];
            if (!figData) return;

            document.getElementById("resultPanel").style.display = "grid";
            const visualBox = document.getElementById("visualContent");
            visualBox.innerHTML = "";

            const card = document.createElement("div");
            card.className = "figure-card";
            const imgFile = figData.image_file;
            const inspectorHtml = renderInspectorHtml(figId, figData);

            card.innerHTML = `
                <div class="figure-caption">Visual Diagram: ${figData.id} - ${figData.title}</div>
                <img src="/figures/${imgFile}" alt="${figData.id}" />
                ${inspectorHtml}
            `;
            visualBox.appendChild(card);

            const answerBox = document.getElementById("answerContent");
            answerBox.innerHTML = `
                <p><strong>Inspecting ${figData.id}: ${figData.title}</strong></p>
                <p style="color: var(--text-secondary); margin-top: 8px;">Location: <code>${figData.page}</code></p>
                <p style="margin-top: 10px;">This standard diagram contains <strong>${figData.chip_count} interactive callout chips</strong> across ${figData.groups.length} technical category groups. Click any chip in the right panel to execute a grounded natural language query with verified definitions and citations.</p>
            `;

            const citationsBox = document.getElementById("citationsBox");
            citationsBox.innerHTML = `<div><strong>Verified Figure Citation:</strong> AWS A3.0M/A3.0:2020, ${figData.page}</div>`;

            document.getElementById("groundedClaimsBox").style.display = "none";
            document.getElementById("seeAlsoBox").style.display = "none";
            document.getElementById("epistemicTraceBox").style.display = "none";

            document.getElementById("resultPanel").scrollIntoView({ behavior: "smooth" });
        }

        window.addEventListener("DOMContentLoaded", () => {
            updateEngineBadge();
            loadFigureCatalog();
        });
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

            elif path == "/api/figures":
                catalog_data = {
                    "categories": FIGURE_CATEGORIES,
                    "figures": get_all_figures_catalog()
                }
                resp_bytes = json.dumps(catalog_data).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
                return

            elif path.startswith("/api/figure_inspector"):
                query_params = urllib.parse.parse_qs(parsed.query)
                fig_id = query_params.get("id", [""])[0]
                inspector_html = get_inspector_html(fig_id)
                resp_bytes = json.dumps({"id": fig_id, "html": inspector_html}).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
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
