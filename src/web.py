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

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

from src.config import (
    BASE_DIR,
    PARSED_FIGURES_DIR,
    PARSED_TABLES_DIR,
    DEFAULT_ENGINE,
    DEEPSEEK_MODEL,
    DEEPSEEK_BASE_URL,
    GEMINI_MODEL,
    GEMINI_BASE_URL,
    CUSTOM_MODEL,
    CUSTOM_BASE_URL,
    DEEPSEEK_API_KEY,
    GEMINI_API_KEY,
    CUSTOM_API_KEY,
    ALLOWED_WEB_ORIGINS
)
from src.security_boundaries import AssetStore, canonical_origin, validate_local_request, validate_model_endpoint
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
        .figure-img-container {
            position: relative;
            display: inline-block;
            cursor: zoom-in;
            border-radius: 6px;
            overflow: hidden;
            width: 100%;
        }
        .zoom-badge {
            position: absolute;
            top: 10px;
            right: 10px;
            background: rgba(10, 15, 29, 0.85);
            border: 1px solid var(--border-color);
            color: var(--accent-cyan);
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 12px;
            pointer-events: none;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .image-modal {
            display: none;
            position: fixed;
            z-index: 9999;
            left: 0;
            top: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(10, 15, 29, 0.94);
            backdrop-filter: blur(8px);
            flex-direction: column;
        }
        .modal-controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 24px;
            background: var(--bg-card);
            border-bottom: 1px solid var(--border-color);
        }
        .modal-title {
            font-size: 15px;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        .modal-btn {
            background: var(--bg-elevated);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px 14px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .modal-btn:hover {
            border-color: var(--accent-cyan);
            color: var(--accent-cyan);
        }
        .modal-btn.close-btn {
            background: rgba(248, 113, 113, 0.15);
            border-color: #f87171;
            color: #f87171;
            font-size: 18px;
            padding: 3px 12px;
        }
        .modal-btn.close-btn:hover {
            background: #f87171;
            color: #fff;
        }
        .modal-viewport {
            flex: 1;
            overflow: hidden;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: grab;
            user-select: none;
        }
        .modal-viewport:active {
            cursor: grabbing;
        }
        #modalStage {
            position: relative;
            display: inline-block;
            transform-origin: center center;
            transition: transform 0.08s ease-out;
            will-change: transform;
            cursor: grab;
        }
        #modalStage:active {
            cursor: grabbing;
        }
        #modalImg {
            max-width: 84vw;
            max-height: 82vh;
            object-fit: contain;
            display: block;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
            border-radius: 6px;
            background: #ffffff;
        }
        #modalSvgOverlay {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
        }
        .highlight-rect {
            fill: rgba(56, 189, 248, 0.12);
            stroke: #38bdf8;
            stroke-width: 4;
            stroke-dasharray: 10, 5;
            filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.8));
            animation: pulseHighlight 2s infinite ease-in-out;
        }
        @keyframes pulseHighlight {
            0% {
                stroke: #38bdf8;
                stroke-width: 4;
                fill: rgba(56, 189, 248, 0.10);
            }
            50% {
                stroke: #4ade80;
                stroke-width: 6;
                fill: rgba(74, 222, 128, 0.22);
                filter: drop-shadow(0 0 18px rgba(74, 222, 128, 0.95));
            }
            100% {
                stroke: #38bdf8;
                stroke-width: 4;
                fill: rgba(56, 189, 248, 0.10);
            }
        }
        .highlight-badge-pill {
            background: rgba(14, 165, 233, 0.95);
            color: #ffffff;
            font-size: 12px;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 14px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
            display: inline-flex;
            align-items: center;
            gap: 5px;
            border: 1px solid rgba(255, 255, 255, 0.4);
            pointer-events: auto;
        }
        .chip-focus-btn {
            margin-left: 5px;
            font-size: 11px;
            opacity: 0.8;
            padding: 1px 4px;
            border-radius: 4px;
            transition: all 0.15s;
            cursor: pointer;
            display: inline-block;
        }
        .chip-focus-btn:hover {
            opacity: 1;
            transform: scale(1.3);
            background: rgba(56, 189, 248, 0.25);
        }
        .modal-hint {
            padding: 10px;
            text-align: center;
            font-size: 12px;
            color: var(--text-secondary);
            background: var(--bg-primary);
            border-top: 1px solid var(--border-color);
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
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap;">
            <button id="settingsBtn" onclick="toggleSettingsDrawer()" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: var(--accent-cyan); padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; transition: all 0.2s;" title="Configure dynamic API keys and custom model endpoints">⚙️ Model & API Keys</button>
            <a href="/api/benchmark" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 12px; font-weight: 600; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); padding: 4px 10px; border-radius: 12px; transition: all 0.2s;" title="View all 50 gold standard test queries and expected citations">📊 50-Item Benchmark JSON</a>
            <div class="engine-badge" id="activeBadge">Engine: DeepSeek</div>
        </div>
    </div>

    <div class="container">
        <!-- Dynamic API Key & Custom Model Configuration Drawer -->
        <div id="settingsDrawer" class="search-card" style="display: none; border: 1px solid var(--accent-cyan); background: #0c1527;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 16px; font-weight: 700; color: var(--accent-cyan);">⚙️ Dynamic Model & API Key Configuration</span>
                    <span style="font-size: 11px; background: rgba(56, 189, 248, 0.15); color: var(--accent-cyan); padding: 2px 8px; border-radius: 12px; font-weight: 600;">Browser Storage (localStorage)</span>
                </div>
                <button onclick="toggleSettingsDrawer()" style="background: transparent; border: none; color: var(--text-secondary); cursor: pointer; font-size: 20px; line-height: 1;" title="Close">&times;</button>
            </div>
            <p style="font-size: 12.5px; color: var(--text-secondary); margin-bottom: 16px;">
                Optionally supply custom API keys or configure an OpenAI-compatible endpoint (OpenAI, Ollama, Groq, OpenRouter, vLLM). Keys are stored locally in your browser and sent only with query requests, never written to disk or git.
            </p>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 14px;">
                <!-- DeepSeek Config -->
                <div style="background: var(--bg-card); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="color: #38bdf8; font-size: 13.5px;">DeepSeek Backend</strong>
                        <span id="deepseekEnvStatus" style="font-size: 11px; color: #94a3b8;">Checking...</span>
                    </div>
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Custom API Key (sk-...):</label>
                    <div style="display: flex; gap: 6px; margin-bottom: 8px;">
                        <input type="password" id="cfgDeepseekKey" placeholder="Leave blank to use server .env" style="flex: 1; padding: 6px 10px; font-size: 12.5px;" />
                        <button onclick="toggleKeyVisibility('cfgDeepseekKey')" style="padding: 6px 10px; font-size: 12px; background: var(--bg-elevated); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; cursor: pointer;" title="Show/Hide">👁️</button>
                    </div>
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Model Name override:</label>
                    <input type="text" id="cfgDeepseekModel" placeholder="deepseek-chat" style="width: 100%; padding: 6px 10px; font-size: 12.5px;" />
                </div>

                <!-- Gemini Config -->
                <div style="background: var(--bg-card); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="color: #38bdf8; font-size: 13.5px;">Google Gemini Backend</strong>
                        <span id="geminiEnvStatus" style="font-size: 11px; color: #94a3b8;">Checking...</span>
                    </div>
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Custom API Key (AIzaSy...):</label>
                    <div style="display: flex; gap: 6px; margin-bottom: 8px;">
                        <input type="password" id="cfgGeminiKey" placeholder="Leave blank to use server .env" style="flex: 1; padding: 6px 10px; font-size: 12.5px;" />
                        <button onclick="toggleKeyVisibility('cfgGeminiKey')" style="padding: 6px 10px; font-size: 12px; background: var(--bg-elevated); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; cursor: pointer;" title="Show/Hide">👁️</button>
                    </div>
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Model Name override:</label>
                    <input type="text" id="cfgGeminiModel" placeholder="gemini-2.0-flash" style="width: 100%; padding: 6px 10px; font-size: 12.5px;" />
                </div>

                <!-- Custom / OpenAI Config -->
                <div style="background: var(--bg-card); padding: 14px; border-radius: 8px; border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="color: #38bdf8; font-size: 13.5px;">Custom / OpenAI Compatible</strong>
                        <span id="customEnvStatus" style="font-size: 11px; color: #94a3b8;">Checking...</span>
                    </div>
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Base URL:</label>
                    <input type="text" id="cfgCustomBaseUrl" placeholder="https://api.openai.com/v1 or http://localhost:11434/v1" style="width: 100%; padding: 6px 10px; font-size: 12.5px; margin-bottom: 8px;" />
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">API Key (sk-... / ollama):</label>
                    <div style="display: flex; gap: 6px; margin-bottom: 8px;">
                        <input type="password" id="cfgCustomKey" placeholder="sk-... (optional for local Ollama)" style="flex: 1; padding: 6px 10px; font-size: 12.5px;" />
                        <button onclick="toggleKeyVisibility('cfgCustomKey')" style="padding: 6px 10px; font-size: 12px; background: var(--bg-elevated); border: 1px solid var(--border-color); color: var(--text-secondary); border-radius: 6px; cursor: pointer;" title="Show/Hide">👁️</button>
                    </div>
                    <label style="font-size: 11.5px; color: var(--text-secondary); display: block; margin-bottom: 4px;">Model Name:</label>
                    <input type="text" id="cfgCustomModel" placeholder="gpt-4o-mini or llama3" style="width: 100%; padding: 6px 10px; font-size: 12.5px;" />
                </div>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 14px;">
                <button onclick="clearCustomSettings()" style="background: var(--bg-elevated); border: 1px solid var(--border-color); color: var(--text-secondary); padding: 7px 14px; border-radius: 6px; font-size: 12.5px; cursor: pointer;">Reset to Defaults</button>
                <button onclick="saveCustomSettings()" style="background: var(--accent-blue); border: none; color: white; padding: 7px 16px; border-radius: 6px; font-size: 12.5px; font-weight: 600; cursor: pointer;">Save Settings</button>
            </div>
        </div>

        <div class="search-card">
            <div class="controls">
                <div class="control-group">
                    <label for="engineSelect">Model Backend:</label>
                    <select id="engineSelect" onchange="updateEngineBadge()">
                        <option value="deepseek">DeepSeek (deepseek-chat)</option>
                        <option value="gemini">Google Gemini (gemini-2.0-flash)</option>
                        <option value="custom">Custom (OpenAI / Ollama / Groq)</option>
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
                <h2>Standard Answer</h2>
                <div id="answerStatusBox" style="font-size: 13px; margin-bottom: 10px;"></div>
                <div class="answer-content" id="answerContent"></div>
                <div class="citations-box" id="citationsBox"></div>
                <div id="groundedClaimsBox" style="margin-top: 16px; display: none;"></div>
                <div id="claimEvidenceBox" role="region" aria-label="Claim evidence links" style="margin-top: 16px; display: none;"></div>
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
            let label = "DeepSeek";
            if (engine === "gemini") label = "Gemini Flash";
            else if (engine === "custom" || engine === "openai") label = "Custom / OpenAI";
            document.getElementById("activeBadge").innerText = "Engine: " + label;
        }

        function toggleSettingsDrawer() {
            const drawer = document.getElementById("settingsDrawer");
            if (drawer.style.display === "none" || !drawer.style.display) {
                drawer.style.display = "block";
                drawer.scrollIntoView({ behavior: "smooth" });
            } else {
                drawer.style.display = "none";
            }
        }

        function toggleKeyVisibility(id) {
            const el = document.getElementById(id);
            if (el) {
                el.type = el.type === "password" ? "text" : "password";
            }
        }

        function readSavedSettings() {
            const saved = JSON.parse(localStorage.getItem("aws_a30_model_settings") || "{}");
            // Purge keys left by earlier versions; current keys stay in page memory.
            delete saved.deepseekKey;
            delete saved.geminiKey;
            delete saved.customKey;
            localStorage.setItem("aws_a30_model_settings", JSON.stringify(saved));
            return saved;
        }

        function loadSavedSettings() {
            try {
                const saved = readSavedSettings();
                if (saved.deepseekModel) document.getElementById("cfgDeepseekModel").value = saved.deepseekModel;
                if (saved.geminiModel) document.getElementById("cfgGeminiModel").value = saved.geminiModel;
                if (saved.customBaseUrl) document.getElementById("cfgCustomBaseUrl").value = saved.customBaseUrl;
                if (saved.customModel) document.getElementById("cfgCustomModel").value = saved.customModel;
                if (saved.selectedEngine) {
                    document.getElementById("engineSelect").value = saved.selectedEngine;
                    updateEngineBadge();
                }
            } catch (e) {
                console.error("Failed to load saved settings", e);
            }
        }

        function saveCustomSettings() {
            const selectedEngine = document.getElementById("engineSelect").value;
            const settings = {
                deepseekModel: document.getElementById("cfgDeepseekModel").value.trim(),
                geminiModel: document.getElementById("cfgGeminiModel").value.trim(),
                customBaseUrl: document.getElementById("cfgCustomBaseUrl").value.trim(),
                customModel: document.getElementById("cfgCustomModel").value.trim(),
                selectedEngine: selectedEngine
            };
            localStorage.setItem("aws_a30_model_settings", JSON.stringify(settings));
            alert("Model settings saved. API keys stay in this page until it is closed or reloaded.");
            toggleSettingsDrawer();
        }

        function clearCustomSettings() {
            if (confirm("Reset custom model & API settings to server defaults?")) {
                localStorage.removeItem("aws_a30_model_settings");
                document.getElementById("cfgDeepseekKey").value = "";
                document.getElementById("cfgDeepseekModel").value = "";
                document.getElementById("cfgGeminiKey").value = "";
                document.getElementById("cfgGeminiModel").value = "";
                document.getElementById("cfgCustomBaseUrl").value = "";
                document.getElementById("cfgCustomKey").value = "";
                document.getElementById("cfgCustomModel").value = "";
                alert("Settings reset to defaults.");
            }
        }

        async function checkConfigStatus() {
            try {
                const res = await fetch("/api/config_status");
                if (!res.ok) return;
                const data = await res.json();
                
                const dsStatus = document.getElementById("deepseekEnvStatus");
                if (dsStatus) {
                    dsStatus.innerHTML = data.deepseek_configured ? '<span style="color:#10b981; font-weight:600;">● Server Active</span>' : '<span style="color:#f87171; font-weight:600;">○ Server Unset</span>';
                }
                const gmStatus = document.getElementById("geminiEnvStatus");
                if (gmStatus) {
                    gmStatus.innerHTML = data.gemini_configured ? '<span style="color:#10b981; font-weight:600;">● Server Active</span>' : '<span style="color:#f87171; font-weight:600;">○ Server Unset</span>';
                }
                const csStatus = document.getElementById("customEnvStatus");
                if (csStatus) {
                    csStatus.innerHTML = data.custom_configured ? '<span style="color:#10b981; font-weight:600;">● Server Active</span>' : '<span style="color:#94a3b8;">○ Unconfigured</span>';
                }
                
                if (!document.getElementById("cfgDeepseekModel").value && data.deepseek_model) {
                    document.getElementById("cfgDeepseekModel").placeholder = data.deepseek_model;
                }
                if (!document.getElementById("cfgGeminiModel").value && data.gemini_model) {
                    document.getElementById("cfgGeminiModel").placeholder = data.gemini_model;
                }
                if (!document.getElementById("cfgCustomModel").value && data.custom_model) {
                    document.getElementById("cfgCustomModel").placeholder = data.custom_model;
                }
                if (!document.getElementById("cfgCustomBaseUrl").value && data.custom_base_url) {
                    document.getElementById("cfgCustomBaseUrl").placeholder = data.custom_base_url;
                }
            } catch (e) {
                console.error("Failed to check config status", e);
            }
        }

        function setQuery(text) {
            document.getElementById("queryInput").value = text;
            executeSearch();
        }

        function appendEvidenceText(parent, tag, text) {
            const node = document.createElement(tag);
            node.textContent = String(text == null ? "" : text);
            parent.appendChild(node);
            return node;
        }

        function appendSourceReference(parent, reference) {
            const label = String(reference);
            // Only catalog-backed figure IDs receive local navigation. Other
            // references remain text; model output never supplies a URL/handler.
            if (/^Figure [AB]\\d+[A-Z]?$/.test(label) && figureMap[label]) {
                const link = appendEvidenceText(parent, "button", label);
                link.type = "button";
                link.className = "pill";
                link.addEventListener("click", () => inspectFigureDirectly(label));
            } else {
                appendEvidenceText(parent, "span", label);
            }
        }

        function evidenceFileName(path) {
            return String(path || "").replaceAll(String.fromCharCode(92), "/").split("/").pop();
        }

        function appendEvidenceImage(parent, path, caption, route) {
            const fileName = evidenceFileName(path);
            if (!fileName) return null;
            // A payload supplies an asset name, never an image URL or handler.
            const url = route + encodeURIComponent(fileName);
            const card = document.createElement("div");
            card.className = "figure-card";
            appendEvidenceText(card, "div", caption).className = "figure-caption";
            const container = document.createElement("div");
            container.className = "figure-img-container";
            container.title = "Click magnifying glass to zoom & pan in high resolution";
            container.tabIndex = 0;
            container.setAttribute("role", "button");
            container.setAttribute("aria-label", "Zoom " + caption);
            const open = () => openImageModal(url, caption);
            container.addEventListener("click", open);
            container.addEventListener("keydown", event => {
                if (event.key === "Enter" || event.key === " ") {event.preventDefault(); open();}
            });
            const image = document.createElement("img");
            image.src = url;
            image.alt = caption;
            container.appendChild(image);
            appendEvidenceText(container, "span", "Zoom / Pan").className = "zoom-badge";
            card.appendChild(container);
            parent.appendChild(card);
            return card;
        }

        function renderClaimEvidence(data) {
            const panel = document.getElementById("claimEvidenceBox");
            panel.textContent = "";
            const links = Array.isArray(data.claim_evidence_links) ? data.claim_evidence_links : [];
            panel.style.display = links.length ? "block" : "none";
            if (!links.length) return;
            const answerWithheld = (data.claim_evidence_assessment || {}).answer_withheld === true;
            appendEvidenceText(panel, "strong", answerWithheld ? "Rejected generated claim diagnostics" : "Claim evidence links");
            if (answerWithheld) appendEvidenceText(panel, "div", "The generated answer was withheld. The text below is rejected output retained for source-identity diagnostics; it is not an asserted answer or proof of support.");
            appendEvidenceText(panel, "div", "Reference resolution, evidence binding, asset availability and claim support are separate results.");
            links.forEach((link, index) => {
                const row = document.createElement("div");
                row.style.cssText = "background: var(--bg-card); border-left: 3px solid #38bdf8; border-radius: 4px; padding: 8px 12px; margin-top: 8px; font-size: 12.5px;";
                appendEvidenceText(row, "strong", "[" + (link.claim_id || "Claim " + (index + 1)) + "] " + (link.claim || ""));
                for (const [label, value] of [
                    ["Reference resolution", link.reference_status || "not_cited"],
                    ["Evidence binding", link.binding_status || "unavailable"],
                    ["Asset availability", link.asset_status || "unavailable"],
                    ["Claim support", link.support_status || "UNASSESSED"]
                ]) appendEvidenceText(row, "div", label + ": " + value);
                const mentions = Array.isArray(link.mentions) ? link.mentions : [];
                mentions.forEach(mention => appendEvidenceText(row, "div", "Citation mention: " + (mention.raw || mention.requested_label || "None explicit")));
                const evidence = Array.isArray(link.ordered_evidence) ? link.ordered_evidence : [];
                evidence.forEach(item => {
                    const source = document.createElement("div");
                    const relationship = item.relationship === "navigation_candidate" ? "Navigation candidate" : item.relationship === "direct" ? "Direct evidence" : "Source reference";
                    appendEvidenceText(source, "span", relationship + ": ");
                    appendSourceReference(source, item.label || item.element_id || "Source reference");
                    appendEvidenceText(source, "div", "Asset availability: " + (item.asset_status || "unavailable"));
                    const anchors = Array.isArray(item.source_anchors) ? item.source_anchors : [];
                    anchors.forEach(anchor => appendEvidenceText(source, "div", "Source anchor: " + [anchor.section_id, anchor.printed_label == null ? "" : "p. " + anchor.printed_label].filter(Boolean).join(", ")));
                    const assets = Array.isArray(item.assets) ? item.assets : [];
                    assets.forEach((asset, assetIndex) => {
                        const orders = Array.isArray(asset.source_anchor_orders) ? asset.source_anchor_orders.join(", ") : "unspecified";
                        appendEvidenceText(source, "div", "Asset " + (assetIndex + 1) + ": " + evidenceFileName(asset.path) + " (" + (asset.kind || "asset") + "; " + (asset.verification_state || "unverified") + "; source anchor orders: " + orders + ")");
                    });
                    row.appendChild(source);
                });
                const diagnostics = Array.isArray(link.diagnostics) ? link.diagnostics : [];
                diagnostics.forEach(code => appendEvidenceText(row, "div", "Diagnostic: " + code));
                panel.appendChild(row);
            });
        }

        function renderAnswerEvidence(data) {
            const assessment = data.answer_assessment || {};
            const reviewed = assessment.status === "SUPPORTED_REVIEWED_FACTS" && assessment.validated === true;
            const outcome = data.answer_outcome || "generated";
            const labels = {
                extractive: reviewed ? "Reviewed source answer" : "Source extract",
                generated: "Generated answer",
                clarification: "More context needed",
                abstention: "Out of scope",
                insufficient_evidence: "Insufficient evidence",
                error: "Answer unavailable"
            };
            const statusBox = document.getElementById("answerStatusBox");
            statusBox.textContent = "";
            appendEvidenceText(statusBox, "strong", labels[outcome] || "Answer");
            let supportText = "Support is not assessed; this answer is not independently verified.";
            if (reviewed) {
                supportText = data.answer_origin === "composed"
                    ? "Composed from reviewed source facts. Claim-to-source bindings were validated."
                    : "Reviewed fact-to-source bindings were validated.";
            } else if (outcome === "abstention") {
                supportText = "The request is outside this standard's supported scope.";
            } else if (outcome === "clarification") {
                supportText = "More application context is needed before selecting an answer.";
            } else if (outcome === "insufficient_evidence") {
                supportText = "The available evidence does not support a complete answer.";
            }
            appendEvidenceText(statusBox, "div", supportText);

            const citationsBox = document.getElementById("citationsBox");
            citationsBox.textContent = "";
            citationsBox.style.display = "block";
            appendEvidenceText(citationsBox, "strong", reviewed ? "Reviewed source references" : "Source references (support not assessed)");
            const citations = data.citations || {};
            for (const [key, label] of [["clauses", "Clauses"], ["pages", "Printed pages"], ["figures", "Figures"], ["tables", "Tables"]]) {
                const row = document.createElement("div");
                appendEvidenceText(row, "strong", label + ": ");
                const references = Array.isArray(citations[key]) ? citations[key] : [];
                if (!references.length) appendEvidenceText(row, "span", "None explicit");
                references.forEach((reference, index) => {
                    if (index) appendEvidenceText(row, "span", ", ");
                    appendSourceReference(row, reference);
                });
                citationsBox.appendChild(row);
            }

            const claimsBox = document.getElementById("groundedClaimsBox");
            claimsBox.textContent = "";
            const claims = Array.isArray(data.grounded_claims) ? data.grounded_claims : [];
            claimsBox.style.display = claims.length ? "block" : "none";
            if (claims.length) {
                appendEvidenceText(claimsBox, "strong", "Claim support (" + claims.length + " statements)");
                claims.forEach((item, index) => {
                    const row = document.createElement("div");
                    row.style.cssText = "background: var(--bg-card); border-left: 3px solid #38bdf8; border-radius: 4px; padding: 8px 12px; margin-top: 8px; font-size: 12.5px;";
                    appendEvidenceText(row, "div", "[Claim " + (index + 1) + "] " + (item.claim || ""));
                    const anchors = Array.isArray(item.anchors) ? item.anchors : [];
                    const hasReferences = anchors.length && !anchors.some(anchor => String(anchor).toLowerCase().includes("inferred from context"));
                    appendEvidenceText(row, "div", reviewed && hasReferences ? "Reviewed source binding" : "Support not assessed; references are not verified.");
                    const references = document.createElement("div");
                    appendEvidenceText(references, "span", "References: ");
                    if (!anchors.length) appendEvidenceText(references, "span", "None explicit");
                    anchors.forEach((anchor, anchorIndex) => {
                        if (anchorIndex) appendEvidenceText(references, "span", ", ");
                        appendSourceReference(references, anchor);
                    });
                    row.appendChild(references);
                    claimsBox.appendChild(row);
                });
            }

            renderClaimEvidence(data);

            const seeAlsoBox = document.getElementById("seeAlsoBox");
            seeAlsoBox.textContent = "";
            const terms = Array.isArray(data.see_also) ? data.see_also : [];
            seeAlsoBox.style.display = terms.length ? "block" : "none";
            if (terms.length) {
                appendEvidenceText(seeAlsoBox, "strong", "Cross-references & related terms");
                terms.forEach(term => {
                    const chip = appendEvidenceText(seeAlsoBox, "button", term);
                    chip.type = "button";
                    chip.className = "pill";
                    chip.addEventListener("click", () => setQuery("What is " + String(term) + "?"));
                });
            }

            const traceBox = document.getElementById("epistemicTraceBox");
            traceBox.textContent = "";
            const trace = data.epistemic_trace;
            const concepts = trace && Array.isArray(trace.concepts_verified) ? trace.concepts_verified : [];
            traceBox.style.display = concepts.length ? "block" : "none";
            if (concepts.length) {
                appendEvidenceText(traceBox, "strong", "Related concepts and source links");
                appendEvidenceText(traceBox, "div", "Graph links support navigation; answer support is assessed separately.");
                concepts.slice(0, 5).forEach(concept => {
                    const row = document.createElement("div");
                    appendEvidenceText(row, "strong", concept.concept || "Related concept");
                    const sources = Array.isArray(concept.primary_evidence) ? concept.primary_evidence : [];
                    sources.slice(0, 3).forEach(source => appendEvidenceText(row, "div", [source.name, source.page].filter(Boolean).join(" · ")));
                    traceBox.appendChild(row);
                });
            }

            const routeBox = document.getElementById("answerRouteBox");
            routeBox.textContent = "";
            const route = data.answer_route || {};
            const evidence = Array.isArray(route.evidence_group) ? route.evidence_group : [];
            routeBox.style.display = evidence.length ? "block" : "none";
            if (evidence.length) {
                appendEvidenceText(routeBox, "strong", "Source links from graph context");
                appendEvidenceText(routeBox, "div", "These links do not measure complete evidence recall or answer correctness.");
                evidence.slice(0, 6).forEach(item => {
                    const element = String(item.element_id || "");
                    const label = item.title || (/^(Clause |Annex |Figure |Table )/.test(element) ? element : "Source reference");
                    appendEvidenceText(routeBox, "div", [label, item.page ? "p. " + item.page : ""].filter(Boolean).join(" · "));
                });
            }
        }

        let searchGeneration = 0;
        async function executeSearch() {
            const query = document.getElementById("queryInput").value.trim();
            if (!query) return;
            const generation = ++searchGeneration;

            const engine = document.getElementById("engineSelect").value;
            const mode = document.getElementById("modeSelect").value;

            // Clear evidence before awaiting a response so previous source links
            // cannot be mistaken for support for this request.
            const resetResultPanels = () => {
                ["citationsBox", "groundedClaimsBox", "claimEvidenceBox", "seeAlsoBox", "epistemicTraceBox", "answerRouteBox", "visualContent"].forEach(id => {
                    const panel = document.getElementById(id);
                    panel.textContent = "";
                    panel.style.display = "none";
                });
                document.getElementById("answerStatusBox").textContent = "";
            };
            resetResultPanels();

            // Keys remain in page memory; only nonsecret model settings are persisted.
            let apiKey = null;
            let modelName = null;
            let baseUrl = null;

            try {
                const saved = readSavedSettings();
                if (engine === "deepseek") {
                    apiKey = document.getElementById("cfgDeepseekKey").value.trim() || null;
                    if (saved.deepseekModel) modelName = saved.deepseekModel;
                } else if (engine === "gemini") {
                    apiKey = document.getElementById("cfgGeminiKey").value.trim() || null;
                    if (saved.geminiModel) modelName = saved.geminiModel;
                } else if (engine === "custom" || engine === "openai") {
                    apiKey = document.getElementById("cfgCustomKey").value.trim() || null;
                    if (saved.customModel) modelName = saved.customModel;
                    if (saved.customBaseUrl) baseUrl = saved.customBaseUrl;
                }
            } catch (e) {}

            document.getElementById("loadingSpinner").style.display = "block";
            document.getElementById("resultPanel").style.display = "none";

            try {
                const payload = { query, engine, mode };
                if (apiKey) payload.api_key = apiKey;
                if (modelName) payload.model_name = modelName;
                if (baseUrl) payload.base_url = baseUrl;

                const response = await fetch("/api/query", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                if (generation !== searchGeneration) return;

                document.getElementById("loadingSpinner").style.display = "none";
                document.getElementById("resultPanel").style.display = "grid";

                if (!response.ok || data.error || data.answer_outcome === "error") {
                    resetResultPanels();
                    document.getElementById("answerStatusBox").textContent = "Answer unavailable";
                    const message = data.error_code === "MODEL_PROVIDER_UNCONFIGURED"
                        ? "Configure an approved model provider before retrying this request."
                        : "The request could not be completed. Check local configuration or try again.";
                    document.getElementById("answerContent").textContent = message;
                    document.getElementById("resultPanel").scrollIntoView({ behavior: "smooth" });
                    return;
                }

                document.getElementById("answerContent").innerText = data.answer || "No text answer returned.";
                renderAnswerEvidence(data);
                document.getElementById("resultPanel").scrollIntoView({ behavior: "smooth" });

                // Render visual evidence
                const visualBox = document.getElementById("visualContent");
                visualBox.innerHTML = "";
                visualBox.style.display = "block";
                let hasVisual = false;

                if (data.resolved_figures && data.resolved_figures.length > 0) {
                    data.resolved_figures.forEach(fig => {
                        const paths = Array.isArray(fig.image_paths) && fig.image_paths.length
                            ? fig.image_paths : fig.image_path ? [fig.image_path] : [];
                        const figKey = String(fig.figure_id || "");
                        const figData = figureMap[figKey] || figureMap[figKey.replace("Figure ", "")] || figureMap["Figure " + figKey];
                        paths.forEach((path, index) => {
                            const caption = "Visual Diagram: " + figKey + (paths.length > 1 ? " (asset " + (index + 1) + " of " + paths.length + ")" : "");
                            const card = appendEvidenceImage(visualBox, path, caption, "/figures/");
                            if (!card) return;
                            hasVisual = true;
                            if (figData && index === 0) {
                                const inspector = document.createElement("div");
                                inspector.innerHTML = renderInspectorHtml(figKey, figData);
                                card.appendChild(inspector);
                            }
                        });
                    });
                }

                if (data.resolved_tables && data.resolved_tables.length > 0) {
                    hasVisual = true;
                    data.resolved_tables.forEach(tbl => {
                        const fileName = evidenceFileName(tbl.table_path);
                        const imagePaths = Array.isArray(tbl.image_paths) ? tbl.image_paths : [];
                        const card = document.createElement("div");
                        card.style.marginTop = "16px";
                        const title = appendEvidenceText(card, "h3", tbl.table_id || "Table source reference");
                        title.style.cssText = "color: var(--accent-cyan); font-size: 15px; margin-bottom: 8px;";
                        const anchors = Array.isArray(tbl.source_anchors) ? tbl.source_anchors : [];
                        anchors.forEach(anchor => appendEvidenceText(card, "div", "Source anchor: " + [anchor.section_id, anchor.printed_label == null ? "" : "p. " + anchor.printed_label].filter(Boolean).join(", ")));
                        if (tbl.asset_status) appendEvidenceText(card, "div", "Asset availability: " + tbl.asset_status);
                        if (fileName) {
                            const content = appendEvidenceText(card, "pre", "Loading table content...");
                            content.className = "table-pre";
                            fetch("/tables/" + encodeURIComponent(fileName))
                                .then(response => {
                                    if (!response.ok) throw new Error("Table export unavailable");
                                    return response.text();
                                })
                                .then(text => {
                                    if (generation === searchGeneration) content.textContent = text;
                                })
                                .catch(() => {
                                    if (generation === searchGeneration) content.textContent = "Table export unavailable.";
                                });
                        } else {
                            appendEvidenceText(card, "div", imagePaths.length
                                ? "No Markdown export available."
                                : "Source-only table reference; no rendered export is available.");
                        }
                        visualBox.appendChild(card);
                        imagePaths.forEach((imagePath, index) => {
                            const caption = "Table Reference Scan: " + tbl.table_id
                                + (imagePaths.length > 1 ? " (asset " + (index + 1) + " of " + imagePaths.length + ")" : "");
                            appendEvidenceImage(visualBox, imagePath, caption, "/tables/");
                        });
                    });
                }

                // Claim assets also cover compact citations and healthy members
                // when legacy whole-set navigation is unavailable.
                const legacyTableIds = new Set((Array.isArray(data.resolved_tables) ? data.resolved_tables : []).map(table => table.table_id));
                const legacyFigureIds = new Set((Array.isArray(data.resolved_figures) ? data.resolved_figures : []).map(figure => figure.figure_id));
                const shownTableAssets = new Set();
                const links = Array.isArray(data.claim_evidence_links) ? data.claim_evidence_links : [];
                links.forEach(link => {
                    const evidence = Array.isArray(link.ordered_evidence) ? link.ordered_evidence : [];
                    evidence.forEach(item => {
                        const element = String(item.element_id || "");
                        const label = String(item.label || element);
                        const isTable = /^table:/.test(element) || /^Table [AD]\\d+$/.test(label);
                        const isFigure = /^figure:/.test(element) || /^Figure [AB]\\d+[A-Z]?$/.test(label);
                        if ((!isTable && !isFigure) || (isTable ? legacyTableIds : legacyFigureIds).has(label)) return;
                        const assets = Array.isArray(item.assets) ? item.assets : [];
                        assets.forEach(asset => {
                            if (asset.kind !== "image" || asset.verification_state !== "verified") return;
                            const key = element + "|" + String(asset.path || "");
                            if (shownTableAssets.has(key)) return;
                            const caption = (isTable ? "Table Reference Scan: " : "Visual Diagram: ") + label + (item.relationship === "navigation_candidate" ? " (navigation candidate)" : "");
                            if (appendEvidenceImage(visualBox, asset.path, caption, isTable ? "/tables/" : "/figures/")) {
                                shownTableAssets.add(key);
                                hasVisual = true;
                            }
                        });
                    });
                });

                if (!hasVisual) {
                    visualBox.innerHTML = '<p style="color: var(--text-secondary); font-size: 14px;">No visual diagrams or tables referenced in this answer.</p>';
                }

            } catch (err) {
                if (generation !== searchGeneration) return;
                resetResultPanels();
                document.getElementById("loadingSpinner").style.display = "none";
                document.getElementById("resultPanel").style.display = "grid";
                document.getElementById("answerStatusBox").textContent = "Answer unavailable";
                document.getElementById("answerContent").textContent = "The request could not be completed. Check local configuration or try again.";
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
                btn.setAttribute("data-category", cat.id);
                btn.onclick = () => filterCategory(cat.id);
                container.appendChild(btn);
            });
        }

        function filterCategory(catId) {
            currentCategory = catId;
            document.querySelectorAll(".category-tab").forEach(tab => {
                tab.classList.toggle("active", tab.getAttribute("data-category") === catId);
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
                    const encodedQuery = encodeURIComponent(c.query || "");
                    const safeLabel = (c.label || "").replace(/'/g, "\\'");
                    const bboxJson = c.bbox ? JSON.stringify(c.bbox) : "null";
                    let focusBtn = "";
                    if (c.bbox) {
                        focusBtn = ` <span class="chip-focus-btn" title="Focus diagram on ${safeLabel}" onclick="event.stopPropagation(); focusFeature('${figData.id || figKey}', '${safeLabel}', ${bboxJson})">🎯</span>`;
                    }
                    html += `<span class="pill" data-query="${encodedQuery}" onclick="event.stopPropagation(); setQuery(decodeURIComponent(this.getAttribute('data-query')))">${c.label}${focusBtn}</span>`;
                });
                html += `
                        </div>
                    </div>
                `;
            });

            html += `</div>`;
            return html;
        }

        function focusFeature(figId, label, bbox) {
            const cleanId = (figId || "").trim();
            const figData = figureMap[cleanId] || figureMap[cleanId.replace("Figure ", "")] || figureMap["Figure " + cleanId];
            if (!figData) return;
            const imgFile = figData.image_file;
            const caption = `<strong>${figData.id}</strong>: ${figData.title} &bull; <span style="color: #4ade80;">🎯 ${label}</span>`;
            openImageModal(`/figures/${imgFile}`, caption, bbox, label);
        }

        function inspectFigureDirectly(figId) {
            const figData = figureMap[figId] || figureMap[figId.replace("Figure ", "")];
            if (!figData) return;
            ++searchGeneration;
            document.getElementById("loadingSpinner").style.display = "none";

            document.getElementById("resultPanel").style.display = "grid";
            const visualBox = document.getElementById("visualContent");
            visualBox.innerHTML = "";

            const imageFiles = Array.isArray(figData.image_files) && figData.image_files.length
                ? figData.image_files : figData.image_file ? [figData.image_file] : [];
            imageFiles.forEach((imageFile, index) => {
                const caption = "Visual Diagram: " + figData.id + " - " + figData.title
                    + (imageFiles.length > 1 ? " (asset " + (index + 1) + " of " + imageFiles.length + ")" : "");
                const card = appendEvidenceImage(visualBox, imageFile, caption, "/figures/");
                if (card && index === 0) {
                    const inspector = document.createElement("div");
                    inspector.innerHTML = renderInspectorHtml(figId, figData);
                    card.appendChild(inspector);
                }
            });

            const answerBox = document.getElementById("answerContent");
            answerBox.innerHTML = `
                <p><strong>Inspecting ${figData.id}: ${figData.title}</strong></p>
                <p style="color: var(--text-secondary); margin-top: 8px;">Location: <code>${figData.page}</code></p>
                <p style="margin-top: 10px;">This standard diagram contains <strong>${figData.chip_count} interactive callout chips</strong> across ${figData.groups.length} technical category groups. Click any chip in the right panel to execute a natural language query with source references.</p>
            `;

            const citationsBox = document.getElementById("citationsBox");
            citationsBox.textContent = "";
            citationsBox.style.display = "block";
            appendEvidenceText(citationsBox, "strong", "Figure source reference: ");
            appendEvidenceText(citationsBox, "span", "AWS A3.0M/A3.0:2020, " + figData.page);

            ["groundedClaimsBox", "claimEvidenceBox", "seeAlsoBox", "epistemicTraceBox", "answerRouteBox"].forEach(id => {
                const panel = document.getElementById(id);
                panel.textContent = "";
                panel.style.display = "none";
            });
            document.getElementById("answerStatusBox").textContent = "Figure inspection";
            visualBox.style.display = "block";

            document.getElementById("resultPanel").scrollIntoView({ behavior: "smooth" });
        }

        // Interactive Zoom & Pan Modal Lightbox with SVG Overlay & Smart Auto-Zoom
        let currentScale = 1;
        let isPanning = false;
        let startX = 0, startY = 0;
        let translateX = 0, translateY = 0;
        let activeBbox = null;
        let activeLabel = null;
        let scrimEnabled = true;

        function openImageModal(imgSrc, caption, bbox, label) {
            const modal = document.getElementById("imageModal");
            const modalImg = document.getElementById("modalImg");
            const modalCaption = document.getElementById("modalCaption");

            modalImg.src = imgSrc;
            modalCaption.innerHTML = caption || "Figure Inspector";
            const validBbox = Array.isArray(bbox) && bbox.length === 4
                && bbox.every(v => typeof v === "number" && Number.isFinite(v))
                && 0 <= bbox[0] && bbox[0] < bbox[2] && bbox[2] <= 1
                && 0 <= bbox[1] && bbox[1] < bbox[3] && bbox[3] <= 1;
            activeBbox = validBbox ? bbox : null;
            activeLabel = validBbox ? (label || null) : null;

            modal.style.display = "flex";
            document.body.style.overflow = "hidden";

            function setupView() {
                const highlightGroup = document.getElementById("svgHighlightGroup");
                const highlightRect = document.getElementById("svgHighlightRect");
                const badge = document.getElementById("svgHighlightBadge");
                const badgeText = document.getElementById("svgBadgeText");
                const svgScrim = document.getElementById("svgScrim");
                const clearBtn = document.getElementById("clearFocusBtn");

                if (activeBbox && Array.isArray(activeBbox) && activeBbox.length === 4) {
                    const [ymin, xmin, ymax, xmax] = activeBbox;
                    const cy = (ymin + ymax) / 2.0;
                    const cx = (xmin + xmax) / 2.0;
                    const boxH = Math.max(0.04, ymax - ymin);
                    const boxW = Math.max(0.04, xmax - xmin);

                    const rw = boxW * 1000;
                    const rh = boxH * 1000;
                    // Contain only the minimum-size display rectangle, not source coordinates.
                    const rx = Math.max(0, Math.min(xmin * 1000, 1000 - rw));
                    const ry = Math.max(0, Math.min(ymin * 1000, 1000 - rh));

                    highlightRect.setAttribute("x", rx);
                    highlightRect.setAttribute("y", ry);
                    highlightRect.setAttribute("width", rw);
                    highlightRect.setAttribute("height", rh);

                    if (badge && badgeText) {
                        badge.setAttribute("x", Math.max(10, Math.min(660, rx)));
                        badge.setAttribute("y", Math.max(10, ry - 44));
                        badgeText.innerText = activeLabel || "Target Feature";
                    }
                    highlightGroup.style.display = "block";

                    if (scrimEnabled && svgScrim) {
                        svgScrim.setAttribute("d", `M0,0 H1000 V1000 H0 Z M${rx},${ry} V${ry + rh} H${rx + rw} V${ry} Z`);
                        svgScrim.style.display = "block";
                    } else if (svgScrim) {
                        svgScrim.style.display = "none";
                    }

                    if (clearBtn) clearBtn.style.display = "inline-block";

                    // Target scale based on bounding box size
                    const fitScale = Math.min(3.2, Math.max(1.8, 0.70 / Math.max(boxW, boxH)));
                    currentScale = fitScale;

                    // Centering translation: offset from image center (0.5, 0.5)
                    const imgW = modalImg.clientWidth || modalImg.offsetWidth || 1000;
                    const imgH = modalImg.clientHeight || modalImg.offsetHeight || 1200;

                    translateX = (0.5 - cx) * imgW * currentScale;
                    translateY = (0.5 - cy) * imgH * currentScale;

                } else {
                    highlightGroup.style.display = "none";
                    if (svgScrim) svgScrim.style.display = "none";
                    if (clearBtn) clearBtn.style.display = "none";
                    currentScale = 1;
                    translateX = 0;
                    translateY = 0;
                }
                updateModalTransform();
            }

            // Invalid or absent focus can reset immediately, even if this image never loads.
            if (!activeBbox || (modalImg.complete && modalImg.naturalWidth > 0)) {
                setupView();
            } else {
                modalImg.onload = setupView;
            }
        }

        function toggleScrim() {
            scrimEnabled = !scrimEnabled;
            const btn = document.getElementById("scrimToggleBtn");
            const svgScrim = document.getElementById("svgScrim");
            if (btn) {
                btn.innerText = scrimEnabled ? "🌓 Scrim: ON" : "🌓 Scrim: OFF";
                btn.style.borderColor = scrimEnabled ? "var(--accent-cyan)" : "var(--border-color)";
            }
            if (svgScrim) {
                if (scrimEnabled && activeBbox) {
                    svgScrim.style.display = "block";
                } else {
                    svgScrim.style.display = "none";
                }
            }
        }

        function clearHighlight() {
            activeBbox = null;
            activeLabel = null;
            document.getElementById("svgHighlightGroup").style.display = "none";
            const svgScrim = document.getElementById("svgScrim");
            if (svgScrim) svgScrim.style.display = "none";
            const clearBtn = document.getElementById("clearFocusBtn");
            if (clearBtn) clearBtn.style.display = "none";
            resetZoom();
        }

        function closeModal() {
            const modal = document.getElementById("imageModal");
            modal.style.display = "none";
            document.body.style.overflow = "auto";
        }

        function zoomImage(delta) {
            currentScale = Math.min(Math.max(0.5, currentScale + delta), 4.5);
            updateModalTransform();
        }

        function resetZoom() {
            currentScale = 1;
            translateX = 0;
            translateY = 0;
            updateModalTransform();
        }

        function updateModalTransform() {
            const stage = document.getElementById("modalStage");
            const zoomLevel = document.getElementById("zoomLevel");
            if (stage) {
                stage.style.transform = `translate(${translateX}px, ${translateY}px) scale(${currentScale})`;
            }
            if (zoomLevel) {
                zoomLevel.innerText = `${Math.round(currentScale * 100)}%`;
            }
        }

        function initModalEvents() {
            const viewport = document.getElementById("modalViewport");
            if (!viewport) return;

            viewport.addEventListener("wheel", (e) => {
                e.preventDefault();
                const delta = e.deltaY < 0 ? 0.2 : -0.2;
                zoomImage(delta);
            }, { passive: false });

            viewport.addEventListener("mousedown", (e) => {
                if (e.button !== 0) return;
                isPanning = true;
                startX = e.clientX - translateX;
                startY = e.clientY - translateY;
            });

            window.addEventListener("mousemove", (e) => {
                if (!isPanning) return;
                translateX = e.clientX - startX;
                translateY = e.clientY - startY;
                updateModalTransform();
            });

            window.addEventListener("mouseup", () => {
                isPanning = false;
            });

            viewport.addEventListener("dblclick", () => {
                if (currentScale <= 1.2) {
                    currentScale = 2.2;
                } else {
                    currentScale = 1;
                    translateX = 0;
                    translateY = 0;
                }
                updateModalTransform();
            });

            window.addEventListener("keydown", (e) => {
                if (e.key === "Escape") {
                    closeModal();
                }
            });
        }

        window.addEventListener("DOMContentLoaded", () => {
            loadSavedSettings();
            updateEngineBadge();
            checkConfigStatus();
            loadFigureCatalog();
            initModalEvents();
        });
    </script>

    <!-- Interactive Zoom & Pan Modal Lightbox with SVG Overlay & Scrim -->
    <div id="imageModal" class="image-modal" onclick="if(event.target===this) closeModal()">
        <div class="modal-controls">
            <span class="modal-title" id="modalCaption">Figure Inspector</span>
            <div style="display: flex; gap: 8px; align-items: center;">
                <button class="modal-btn" id="scrimToggleBtn" onclick="toggleScrim()" title="Toggle Dimming Scrim">🌓 Scrim: ON</button>
                <button class="modal-btn" id="clearFocusBtn" onclick="clearHighlight()" style="display: none;" title="Show Full Diagram">🔍 Show Full</button>
                <button class="modal-btn" onclick="zoomImage(0.25)" title="Zoom In (+)">🔍 +</button>
                <span id="zoomLevel" style="font-size: 13px; color: var(--accent-cyan); min-width: 48px; text-align: center; font-weight: 700;">100%</span>
                <button class="modal-btn" onclick="zoomImage(-0.25)" title="Zoom Out (-)">🔍 -</button>
                <button class="modal-btn" onclick="resetZoom()" title="Reset Zoom">Reset</button>
                <button class="modal-btn close-btn" onclick="closeModal()" title="Close (Esc)">&times;</button>
            </div>
        </div>
        <div class="modal-viewport" id="modalViewport">
            <div id="modalStage">
                <img id="modalImg" src="" alt="Zoomed Diagram" draggable="false" />
                <svg id="modalSvgOverlay" viewBox="0 0 1000 1000" preserveAspectRatio="none">
                    <path id="svgScrim" fill="rgba(15, 23, 42, 0.60)" fill-rule="evenodd" d="M0,0 H1000 V1000 H0 Z" style="display: none;"></path>
                    <g id="svgHighlightGroup" style="display: none;">
                        <rect id="svgHighlightRect" class="highlight-rect" x="0" y="0" width="0" height="0" rx="8"></rect>
                        <foreignObject id="svgHighlightBadge" x="0" y="0" width="340" height="42">
                            <div xmlns="http://www.w3.org/1999/xhtml" class="highlight-badge-pill">
                                <span style="font-size: 13px;">🎯</span>
                                <span id="svgBadgeText" style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 280px;">Target Feature</span>
                            </div>
                        </foreignObject>
                    </g>
                </svg>
            </div>
        </div>
        <div class="modal-hint">
            💡 <strong>Interactive Pan & Zoom:</strong> Drag to pan &bull; Scroll wheel to zoom &bull; Double-click to toggle zoom &bull; 🎯 Focus buttons auto-center sub-panels &bull; Esc to close
        </div>
    </div>

</body>
</html>
"""

class MultimodalRequestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        if getattr(self, "_approved_origin", None):
            self.send_header("Access-Control-Allow-Origin", self._approved_origin)
            self.send_header("Vary", "Origin")
        super().end_headers()

    def _check_request(self):
        self._approved_origin = None
        try:
            self._approved_origin = validate_local_request(
                self.headers, self.server.server_address, self.server.allowed_origins
            )
        except ValueError:
            self.send_error(403, "Request host or origin is not approved")
            return False
        return True

    def _send_json(self, status, value):
        data = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        if not self._check_request():
            return
        requested_headers = {h.strip().lower() for h in self.headers.get("Access-Control-Request-Headers", "").split(",") if h.strip()}
        if (urllib.parse.urlsplit(self.path).path != "/api/query"
                or not self._approved_origin
                or self.headers.get("Access-Control-Request-Method") != "POST"
                or requested_headers - {"content-type"}):
            self.send_error(403, "Preflight is not approved")
            return
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "POST")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, format, *args):
        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format % args))
        sys.stderr.flush()

    def do_GET(self):
        if not self._check_request():
            return
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

            elif path == "/api/config_status":
                status = {
                    "default_engine": DEFAULT_ENGINE,
                    "deepseek_configured": bool(DEEPSEEK_API_KEY),
                    "deepseek_model": DEEPSEEK_MODEL,
                    "gemini_configured": bool(GEMINI_API_KEY),
                    "gemini_model": GEMINI_MODEL,
                    "custom_configured": bool(CUSTOM_API_KEY),
                    "custom_model": CUSTOM_MODEL,
                    "custom_base_url": CUSTOM_BASE_URL,
                }
                resp_bytes = json.dumps(status).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
                return

            elif path == "/api/benchmark":
                benchmark_path = BASE_DIR / "eval" / "gold_benchmark.json"
                if benchmark_path.exists():
                    data = json.loads(benchmark_path.read_text(encoding="utf-8"))
                    resp_bytes = json.dumps(data, indent=2).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(resp_bytes)))
                    self.end_headers()
                    self.wfile.write(resp_bytes)
                    return
                else:
                    self.send_error(404, "Benchmark file not found")
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
                try:
                    _, img_bytes = self.server.asset_stores["figures"].read(path[len("/figures/"):])
                    self.send_response(200)
                    self.send_header("Content-Type", "image/png")
                    self.send_header("Content-Length", str(len(img_bytes)))
                    self.end_headers()
                    self.wfile.write(img_bytes)
                    return
                except (ValueError, OSError):
                    self.send_error(404, "Figure image not found")
                    return

            elif path.startswith("/tables/"):
                try:
                    filename, t_bytes = self.server.asset_stores["tables"].read(path[len("/tables/"):])
                    content_type = "image/png" if filename.lower().endswith(".png") else "text/plain; charset=utf-8"
                    self.send_response(200)
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Length", str(len(t_bytes)))
                    self.end_headers()
                    self.wfile.write(t_bytes)
                    return
                except (ValueError, OSError):
                    self.send_error(404, "Table file not found")
                    return

            self.send_error(404, "Endpoint not found")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_error(500, "Server request failed")

    def do_POST(self):
        if not self._check_request():
            return
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/query":
            try:
                content_types = self.headers.get_all("Content-Type", [])
                lengths = self.headers.get_all("Content-Length", [])
                if len(content_types) != 1 or content_types[0].split(";", 1)[0].strip().lower() != "application/json":
                    self._send_json(415, {"error": "Content-Type must be application/json."})
                    return
                if len(lengths) != 1 or self.headers.get("Transfer-Encoding"):
                    raise ValueError("A single Content-Length is required.")
                content_length = int(lengths[0])
                if not 0 < content_length <= 65536:
                    self._send_json(413, {"error": "Query request exceeds the supported size."})
                    return
                body = self.rfile.read(content_length).decode("utf-8")
                if len(body.encode("utf-8")) != content_length:
                    raise ValueError("Incomplete query request.")
                data = json.loads(body)
                if not isinstance(data, dict):
                    raise ValueError("Query request must be a JSON object.")

                query = data.get("query", "")
                engine = data.get("engine", DEFAULT_ENGINE)
                mode = data.get("mode", "mix")
                api_key = data.get("api_key") or None
                model_name = data.get("model_name") or None
                base_url = data.get("base_url") or None
                evidence_version = data.get("evidence_version", "v1")
                v2_reader = data.get("v2_reader", "extractive")
                if (not isinstance(evidence_version, str) or not isinstance(v2_reader, str)
                        or evidence_version not in {"v1", "v2"} or v2_reader not in {"extractive", "local"}):
                    raise ValueError("Unsupported evidence version or reader.")

                endpoints = {"deepseek": DEEPSEEK_BASE_URL, "gemini": GEMINI_BASE_URL,
                             "custom": CUSTOM_BASE_URL, "openai": CUSTOM_BASE_URL}
                if not isinstance(engine, str) or engine.lower() not in endpoints:
                    raise ValueError("Unsupported model engine.")
                engine = engine.lower()
                if not isinstance(query, str) or not query.strip() or len(query) > 16384:
                    raise ValueError("Query must be nonempty text within 16384 characters.")
                if not isinstance(mode, str) or mode not in {"mix", "local", "global", "naive"}:
                    raise ValueError("Unsupported retrieval mode.")
                if any(value is not None and not isinstance(value, str) for value in (api_key, model_name, base_url)):
                    raise ValueError("Model settings must be strings.")
                base_url = validate_model_endpoint(base_url, endpoints[engine])

                print(f"[API QUERY] Engine={engine}, Mode={mode}")
                version_options = ({"evidence_version": evidence_version, "v2_reader": v2_reader}
                                   if evidence_version == "v2" else {})
                res = run_query(query, mode=mode, engine=engine, api_key=api_key, model_name=model_name, base_url=base_url, **version_options)

                error_status = {
                    "RETRIEVAL_INDEX_MISSING": 503,
                    "TERMINOLOGY_REGISTRY_INVALID": 503,
                    "MODEL_PROVIDER_UNCONFIGURED": 503,
                    "GENERATION_FAILED": 502,
                    "EVIDENCE_BINDING_FAILED": 503,
                    "V2_SOURCE_UNAVAILABLE": 503,
                    "V2_READER_REQUIRED": 422,
                    "V2_READER_FAILED": 502,
                }.get(res.get("error_code"))
                if error_status:
                    self._send_json(error_status, res)
                    return

                resp_bytes = json.dumps(res).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(resp_bytes)))
                self.end_headers()
                self.wfile.write(resp_bytes)
                return
            except (ValueError, UnicodeError) as e:
                self._send_json(400, {"error": str(e)})
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                err_bytes = json.dumps({"error": "Query execution failed."}).encode("utf-8")
                self.send_response(500)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(err_bytes)))
                self.end_headers()
                self.wfile.write(err_bytes)
                return

        self.send_error(404, "Unknown API endpoint")

def run_server(port: int = 8000, open_browser: bool = False):
    server_address = ("127.0.0.1", port)
    allowed_origins = tuple(canonical_origin(value) for value in ALLOWED_WEB_ORIGINS)
    asset_stores = {"figures": AssetStore(PARSED_FIGURES_DIR, {".png"}),
                    "tables": AssetStore(PARSED_TABLES_DIR, {".png", ".md"})}
    httpd = ThreadingHTTPServer(server_address, MultimodalRequestHandler)
    httpd.allowed_origins = allowed_origins
    httpd.asset_stores = asset_stores
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
