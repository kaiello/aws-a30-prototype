"""
extract.py: High-fidelity multimodal extraction for AWS A3.0M/A3.0:2020.
Extracts:
1. Clause 1-4 text definitions (with exact page & clause references)
2. Annex A Tables A1-A5 (Markdown tables preserving headers and process designations)
3. Annex B Figures B1-B60+ (Page renders at 180 DPI + captions & metadata)
"""

import os
import re
import json
import base64
import argparse
from pathlib import Path
import fitz  # PyMuPDF
from src.config import (
    PDF_PATH,
    PARSED_TEXT_FILE,
    PARSED_TABLES_DIR,
    PARSED_FIGURES_DIR,
    ANNEX_B_START_PAGE,
    ANNEX_B_END_PAGE,
    ANNEX_A_START_PAGE,
    GLOSSARY_START_PAGE,
    FIGURE_RENDER_DPI
)

from src.standard_manifest import get_manifest


def clean_text_line(line: str) -> str:
    # Replace non-printable characters and normalize dashes
    line = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', line)
    line = line.replace('\u2014', '—').replace('\u2013', '–')
    # Filter out license stamp lines
    if "Accessed by account:" in line or "IP address:" in line:
        return ""
    return line.strip()

def extract_clause4_glossary(doc: fitz.Document):
    print(f"Extracting Clause 4 Glossary from pages {GLOSSARY_START_PAGE} to {ANNEX_A_START_PAGE - 1}...")
    chunks = []
    
    # Also extract Clauses 1-3 preamble
    preamble_lines = []
    for pno in range(get_manifest().section("Clause 1")["spans"][0]["start_pdf_index"], GLOSSARY_START_PAGE):
        p_text = doc[pno].get_text()
        for l in p_text.split('\n'):
            cleaned = clean_text_line(l)
            if cleaned:
                preamble_lines.append(cleaned)
    
    chunks.append({
        "chunk_id": "clauses_1_to_3_scope",
        "clause": "Clauses 1–3",
        "pdf_page_start": get_manifest().section("Clause 1")["spans"][0]["start_pdf_index"],
        "pdf_page_end": GLOSSARY_START_PAGE - 1,
        "printed_pages": "1–4",
        "title": "Scope, Normative References, and General Requirements",
        "content": "\n".join(preamble_lines),
        "cross_references": []
    })

    # Clause 4 terms
    for pno in range(GLOSSARY_START_PAGE, ANNEX_A_START_PAGE):
        page = doc[pno]
        raw_text = page.get_text()
        lines = [clean_text_line(l) for l in raw_text.split('\n')]
        lines = [l for l in lines if l]
        
        # Determine printed page
        printed_page = int(get_manifest().document["pages"][pno]["printed_label"])
        filtered_lines = []
        for l in lines:
            if re.match(r'^\d+$', l):
                continue
            if "CLAUSE 4. GLOSSARY" in l or "AWS A3.0M/A3.0:2020" in l:
                continue
            filtered_lines.append(l)
        
            
        page_content = " ".join(filtered_lines)
        
        # Find cross-references
        fig_refs = re.findall(r'Figure\s+B\d+(?:\([A-Z0-9]+\))?', page_content, re.IGNORECASE)
        table_refs = re.findall(r'Table\s+A\d+', page_content, re.IGNORECASE)
        see_refs = re.findall(r'See\s+([A-Za-z0-9\s,\–\-]+?)(?:\.|$)', page_content)
        
        chunk = {
            "chunk_id": f"clause_4_p{printed_page}",
            "clause": "Clause 4",
            "pdf_page": pno,
            "printed_page": printed_page,
            "title": f"Clause 4 Glossary (p. {printed_page})",
            "content": f"[AWS A3.0:2020 Clause 4, p. {printed_page}]\n" + "\n".join(filtered_lines),
            "cross_references": list(set(fig_refs + table_refs))
        }
        chunks.append(chunk)

    PARSED_TEXT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PARSED_TEXT_FILE, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Extracted {len(chunks)} text chunks to {PARSED_TEXT_FILE}")

def extract_annex_a_tables(doc: fitz.Document):
    print(f"Extracting Annex A Tables from pages {ANNEX_A_START_PAGE} to {ANNEX_B_START_PAGE - 1}...")
    PARSED_TABLES_DIR.mkdir(parents=True, exist_ok=True)
    table_chunks = []
    
    current_table = "Table A1"
    table_lines = {label: [] for label in get_manifest().labels("tables") if label.startswith("Table A")}
    
    table_pages = sorted({a["pdf_index"] for label in get_manifest().labels("tables")
                          if label.startswith("Table A") for a in get_manifest().anchors(label)})
    for pno in table_pages:
        text = doc[pno].get_text()
        for line in text.split('\n'):
            l = clean_text_line(line)
            if not l or "AWS A3.0M/A3.0:2020" in l or "ANNEx A" in l.upper():
                continue
            
            # Table switch detection
            caption = re.sub(r"\s+\(Continued\)$", "", l)
            if caption in table_lines:
                current_table = caption
            
            table_lines[current_table].append(l)

    for t_id, lines in table_lines.items():
        if not lines:
            continue
        md_file = PARSED_TABLES_DIR / f"{t_id.lower().replace(' ', '_')}.md"
        content_header = f"# AWS A3.0:2020 Annex A - {t_id}\n\n"
        content_body = "\n".join(lines)
        full_content = content_header + content_body
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(full_content)
        
        table_chunks.append({
            "chunk_id": f"annex_a_{t_id.lower().replace(' ', '_')}",
            "clause": "Annex A",
            "table_id": t_id,
            "title": f"Annex A: {t_id}",
            "content": full_content,
            "file_path": str(md_file)
        })

    annex_a_jsonl = PARSED_TABLES_DIR / "annex_a_tables.jsonl"
    with open(annex_a_jsonl, "w", encoding="utf-8") as f:
        for tc in table_chunks:
            f.write(json.dumps(tc, ensure_ascii=False) + "\n")
    print(f"Extracted {len(table_chunks)} tables to {PARSED_TABLES_DIR}")

def extract_annex_b_figures(doc: fitz.Document, render_images: bool = True):
    print(f"Extracting Annex B Figures from pages {ANNEX_B_START_PAGE} to {ANNEX_B_END_PAGE}...")
    PARSED_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    figures = []
    
    fig_title_regex = re.compile(r'Figure\s+(B\d+)(?:\s*\(Continued\))?\s*[—–\-]?\s*(.*)', re.IGNORECASE)
    
    for pno in range(ANNEX_B_START_PAGE, ANNEX_B_END_PAGE + 1):
        page = doc[pno]
        text = page.get_text()
        
        # Check printed page number
        lines = [clean_text_line(l) for l in text.split('\n')]
        lines = [l for l in lines if l]
        
        printed_page = int(get_manifest().document["pages"][pno]["printed_label"])
            
        # Detect figure title
        fig_id = None
        fig_title = "Welding Diagram"
        for l in lines:
            m = fig_title_regex.search(l)
            if m:
                fig_id = f"Figure {m.group(1).upper()}"
                fig_title = m.group(2).strip() or fig_title
                break
        
        if not fig_id:
            # Check if this is an untitled page in Annex B
            fig_id = f"Figure_AnnexB_p{pno}"

        image_filename = f"{fig_id.replace(' ', '_')}_p{pno}.png"
        image_path = PARSED_FIGURES_DIR / image_filename
        
        if render_images and not image_path.exists():
            pix = page.get_pixmap(dpi=FIGURE_RENDER_DPI)
            pix.save(str(image_path))
            
        fig_data = {
            "chunk_id": f"annex_b_{fig_id.lower().replace(' ', '_')}_p{pno}",
            "clause": "Annex B",
            "figure_id": fig_id,
            "title": f"{fig_id}: {fig_title}",
            "pdf_page": pno,
            "printed_page": printed_page,
            "image_path": str(image_path),
            "content": f"[AWS A3.0:2020 Annex B, {fig_id}, p. {printed_page}]\nTitle: {fig_title}\nCaptions and text:\n" + "\n".join(lines)
        }
        figures.append(fig_data)
        
        # Save per-figure metadata
        meta_file = PARSED_FIGURES_DIR / f"{fig_id.replace(' ', '_')}_p{pno}.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(fig_data, f, indent=2, ensure_ascii=False)

    annex_b_jsonl = PARSED_FIGURES_DIR / "annex_b_figures.jsonl"
    with open(annex_b_jsonl, "w", encoding="utf-8") as f:
        for fd in figures:
            f.write(json.dumps(fd, ensure_ascii=False) + "\n")
    print(f"Extracted {len(figures)} figure pages/renders to {PARSED_FIGURES_DIR}")

def main():
    parser = argparse.ArgumentParser(description="Extract multimodal assets from AWS A3.0 PDF")
    parser.add_argument("--skip-render", action="store_true", help="Skip rendering PNG images for figures")
    args = parser.parse_args()

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Source PDF not found at {PDF_PATH}")

    doc = fitz.open(str(PDF_PATH))
    print(f"Opened PDF: {PDF_PATH} ({len(doc)} pages)")
    
    extract_clause4_glossary(doc)
    extract_annex_a_tables(doc)
    extract_annex_b_figures(doc, render_images=not args.skip_render)
    print("Multimodal extraction complete!")

if __name__ == "__main__":
    main()
