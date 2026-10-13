"""
demonstrator.py: Interactive Multimodal NLQ Demonstrator for AWS A3.0M/A3.0:2020.
Features:
- Single-query CLI and Interactive REPL mode
- Side-by-side terminal card output with citations & asset links
- Standalone HTML card viewer generation (--html) with inline image rendering
"""

import os
import sys
import argparse
import base64
from pathlib import Path
from src.query import run_query
from src.config import BASE_DIR, DEFAULT_ENGINE

# ... rest of HTML template and generators ...


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AWS A3.0 Multimodal NLQ Card</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 40px;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            max-width: 900px;
            margin: 0 auto;
            padding: 32px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
        }}
        h1 {{
            color: #38bdf8;
            font-size: 24px;
            margin-top: 0;
            border-bottom: 1px solid #334155;
            padding-bottom: 16px;
        }}
        .badge {{
            display: inline-block;
            background: #0284c7;
            color: #fff;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            margin-bottom: 16px;
        }}
        .answer-box {{
            background: #0f172a;
            border-left: 4px solid #38bdf8;
            padding: 20px;
            border-radius: 4px;
            line-height: 1.6;
            font-size: 16px;
            margin-bottom: 24px;
        }}
        .citations-section {{
            background: #1e293b;
            border: 1px solid #475569;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 24px;
        }}
        .citations-section h3 {{
            margin-top: 0;
            color: #94a3b8;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .figure-container {{
            margin-top: 24px;
            text-align: center;
        }}
        .figure-container img {{
            max-width: 100%;
            border: 1px solid #475569;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            margin-top: 12px;
        }}
        .figure-caption {{
            color: #cbd5e1;
            font-size: 14px;
            margin-top: 8px;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="card">
        <span class="badge">AWS A3.0M/A3.0:2020 Standard</span>
        <h1>{query}</h1>
        
        <div class="answer-box">
            {answer_html}
        </div>

        <div class="citations-section">
            <h3>Verified Citations & Provenance</h3>
            <div><strong>Clauses:</strong> {clauses}</div>
            <div><strong>Pages:</strong> {pages}</div>
            <div><strong>Tables:</strong> {tables}</div>
            <div><strong>Figures:</strong> {figures}</div>
        </div>

        {figures_html}
        {tables_html}
    </div>
</body>
</html>
"""

def generate_html_card(result: dict, output_path: Path):
    query = result["query"]
    answer_html = result["answer"].replace("\n", "<br/>")
    
    citations = result.get("citations", {})
    clauses = ", ".join(citations.get("clauses", [])) or "None explicit"
    pages = ", ".join(map(str, citations.get("pages", []))) or "None explicit"
    tables = ", ".join(citations.get("tables", [])) or "None"
    figures = ", ".join(citations.get("figures", [])) or "None"

    figures_html = ""
    for fig in result.get("resolved_figures", []):
        img_path = Path(fig["image_path"])
        if img_path.exists():
            with open(img_path, "rb") as img_f:
                b64 = base64.b64encode(img_f.read()).decode("utf-8")
            figures_html += f"""
            <div class="figure-container">
                <div class="figure-caption">Visual Evidence: {fig['figure_id']}</div>
                <img src="data:image/png;base64,{b64}" alt="{fig['figure_id']}" />
            </div>
            """

    tables_html = ""
    for tbl in result.get("resolved_tables", []):
        t_path = Path(tbl["table_path"])
        if t_path.exists():
            content = t_path.read_text(encoding="utf-8")
            tables_html += f"""
            <div style="margin-top: 24px;">
                <h3 style="color: #38bdf8;">{tbl['table_id']} Excerpt</h3>
                <pre style="background: #0f172a; padding: 16px; border-radius: 8px; overflow-x: auto;">{content}</pre>
            </div>
            """

    html = HTML_TEMPLATE.format(
        query=query,
        answer_html=answer_html,
        clauses=clauses,
        pages=pages,
        tables=tables,
        figures=figures,
        figures_html=figures_html,
        tables_html=tables_html
    )
    
    output_path.write_text(html, encoding="utf-8")
    return output_path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def print_terminal_card(result: dict):
    border = "+" + "-"*76 + "+"
    print("\n" + border)
    print(f"| QUERY: {result['query'][:68]:<68} |")
    print("+" + "-"*76 + "+")
    print("| ANSWER:                                                                    |")
    for line in result['answer'].split('\n'):
        while len(line) > 72:
            chunk = line[:72]
            line = line[72:]
            print(f"|   {chunk:<72} |")
        print(f"|   {line:<72} |")
        
    print("+" + "-"*76 + "+")
    c = result.get('citations', {})
    cit_str = f"Clauses: {c.get('clauses', [])} | Figs: {c.get('figures', [])} | Tables: {c.get('tables', [])}"
    print(f"| CITATIONS: {cit_str[:64]:<64} |")
    
    if result.get("resolved_figures"):
        print("+" + "-"*76 + "+")
        print("| VISUAL EVIDENCE (FIGURE CROPS):                                            |")
        for fig in result["resolved_figures"]:
            line = f"{fig['figure_id']} -> {fig['image_path']}"
            print(f"|   {line[:72]:<72} |")
            
    if result.get("resolved_tables"):
        print("+" + "-"*76 + "+")
        print("| TABULAR EVIDENCE:                                                          |")
        for tbl in result["resolved_tables"]:
            line = f"{tbl['table_id']} -> {tbl['table_path']}"
            print(f"|   {line[:72]:<72} |")
            
    print(border + "\n")

def run_demonstrator(query: str, generate_html: bool = False, mode: str = "mix", engine: str = DEFAULT_ENGINE):
    res = run_query(query, mode=mode, engine=engine)
    print_terminal_card(res)
    
    if generate_html:
        out_html = BASE_DIR / "viewer.html"
        generate_html_card(res, out_html)
        print(f"[HTML VIEWER GENERATED]: file:///{out_html.as_posix()}")

def interactive_loop(generate_html: bool = False, engine: str = DEFAULT_ENGINE):
    print("\n" + "="*70)
    print(f"AWS A3.0 Multimodal NLQ Interactive Demonstrator (Engine: {engine})")
    print("Type your welding query, or 'exit' / 'quit' to stop.")
    print("="*70 + "\n")
    
    while True:
        try:
            q = input("\nEnter Query > ").strip()
            if not q:
                continue
            if q.lower() in ["exit", "quit", "q"]:
                print("Exiting demonstrator.")
                break
            run_demonstrator(q, generate_html=generate_html, engine=engine)
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

def main():
    parser = argparse.ArgumentParser(description="AWS A3.0 Multimodal NLQ Demonstrator")
    parser.add_argument("query", nargs="?", type=str, help="Single query to execute")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive query loop")
    parser.add_argument("--html", action="store_true", help="Generate browser-friendly HTML card (viewer.html)")
    parser.add_argument("--mode", type=str, default="mix", help="LightRAG query mode (mix/local/global)")
    parser.add_argument("--engine", type=str, default=DEFAULT_ENGINE, choices=["deepseek", "gemini"], help="Inference engine")
    args = parser.parse_args()

    if args.interactive or not args.query:
        interactive_loop(generate_html=args.html, engine=args.engine)
    else:
        run_demonstrator(args.query, generate_html=args.html, mode=args.mode, engine=args.engine)

if __name__ == "__main__":
    main()
