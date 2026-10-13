"""
vlm_extract.py: Multimodal Vision Perception Pipeline for AWS A3.0 Annex B Diagrams.
Analyzes rendered engineering diagrams (PNG) using Gemini Flash Vision or local Ollama (qwen3-vl).
Extracts fine-grained anatomical components, geometric callouts, and technical descriptions
into structured JSON and LightRAG-ingestible knowledge chunks.
"""

import os
import sys
import json
import base64
import re
import argparse
from pathlib import Path
from openai import OpenAI
import requests

from src.config import (
    PARSED_FIGURES_DIR,
    PARSED_ANATOMY_DIR,
    GEMINI_API_KEY,
    GEMINI_BASE_URL,
    GEMINI_MODEL,
    OLLAMA_BASE_URL,
    VLM_MODEL
)

VLM_SYSTEM_PROMPT = """You are an expert welding engineer and technical standards parser analyzing official diagrams from AWS A3.0M/A3.0:2020 Standard Welding Terms and Definitions.
Analyze the provided engineering diagram and extract its exact anatomical elements with high precision.
Output ONLY a valid JSON object matching this schema:
{
  "figure_id": "Figure B<N>",
  "title": "<Official figure title as shown in heading>",
  "components": ["<List of all labeled sub-parts, weld features, or anatomical terms visible in the diagram>"],
  "geometric_features": ["<List of all angular measurements, dimensions, axes, or orientation callouts>"],
  "description": "<Detailed 2-3 sentence technical description of the diagram and its normative engineering meaning>",
  "cross_reference_terms": ["<Related AWS A3.0 terms illustrated by this figure>"]
}
Do not wrap your JSON in any explanation or preamble. Return ONLY the raw JSON string."""

def encode_image(image_path: Path) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def analyze_figure_gemini(image_path: Path, client: OpenAI) -> dict:
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model=GEMINI_MODEL,
        messages=[
            {"role": "system", "content": VLM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Extract the anatomical components and geometric features from this AWS A3.0 diagram ({image_path.name})."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0.0
    )
    
    content = response.choices[0].message.content.strip()
    # Clean json formatting wrappers if present
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
    return json.loads(content)

def analyze_figure_ollama(image_path: Path) -> dict:
    base64_image = encode_image(image_path)
    url = f"{OLLAMA_BASE_URL}/api/chat"
    payload = {
        "model": VLM_MODEL,
        "messages": [
            {"role": "system", "content": VLM_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Extract the anatomical components and geometric features from this AWS A3.0 diagram ({image_path.name}).",
                "images": [base64_image]
            }
        ],
        "stream": False,
        "options": {"temperature": 0.0}
    }
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    content = data["message"]["content"].strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\n?", "", content)
        content = re.sub(r"\n?```$", "", content)
    return json.loads(content)

def process_figures(figures: list = None, backend: str = "auto", output_dir: Path = PARSED_ANATOMY_DIR):
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Select backend
    use_gemini = False
    if backend == "gemini" or (backend == "auto" and GEMINI_API_KEY):
        if not GEMINI_API_KEY:
            print("[ERROR] GEMINI_API_KEY not configured for Gemini VLM backend!")
            sys.exit(1)
        client = OpenAI(api_key=GEMINI_API_KEY, base_url=GEMINI_BASE_URL)
        use_gemini = True
        print(f"Using Gemini Flash Vision ({GEMINI_MODEL}) backend")
    else:
        print(f"Using local Ollama ({VLM_MODEL}) backend")

    # Locate figure PNGs
    all_pngs = sorted(list(PARSED_FIGURES_DIR.glob("Figure_B*.png")))
    if not all_pngs:
        print(f"[ERROR] No rendered figures found in {PARSED_FIGURES_DIR}")
        return

    targets = []
    if figures:
        for f in figures:
            clean_f = f.upper() if f.upper().startswith("B") else f"B{f}"
            matches = [p for p in all_pngs if f"Figure_{clean_f}_" in p.name]
            targets.extend(matches)
    else:
        targets = all_pngs

    print(f"Analyzing {len(targets)} AWS A3.0 diagrams for visual anatomy...")
    
    anatomy_records = []
    for idx, png_path in enumerate(targets, 1):
        print(f"[{idx}/{len(targets)}] Processing {png_path.name}...")
        try:
            if use_gemini:
                data = analyze_figure_gemini(png_path, client)
            else:
                data = analyze_figure_ollama(png_path)
                
            data["source_image"] = str(png_path)
            data["image_file"] = png_path.name
            
            # Save individual JSON
            base_name = png_path.stem
            out_file = output_dir / f"{base_name}_anatomy.json"
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
                
            anatomy_records.append(data)
            print(f"  -> Extracted {len(data.get('components', []))} components, {len(data.get('geometric_features', []))} features.")
        except Exception as e:
            print(f"  -> [WARNING] Failed to process {png_path.name}: {e}")

    # Generate merged LightRAG chunks file
    chunks_file = output_dir / "annex_b_anatomy_chunks.jsonl"
    with open(chunks_file, "w", encoding="utf-8") as f:
        for item in anatomy_records:
            comp_str = ", ".join(item.get("components", []))
            geom_str = ", ".join(item.get("geometric_features", []))
            terms_str = ", ".join(item.get("cross_reference_terms", []))
            
            content = (
                f"[AWS A3.0:2020 Annex B Visual Anatomy - {item.get('figure_id', 'Figure')}: {item.get('title', '')}]\n"
                f"File: {item.get('image_file', '')}\n"
                f"Description: {item.get('description', '')}\n"
                f"Visual Labeled Components: {comp_str}\n"
                f"Geometric & Axis Features: {geom_str}\n"
                f"Illustrated AWS Standard Terms: {terms_str}\n"
            )
            
            chunk_record = {
                "chunk_id": f"anatomy_{item.get('figure_id', 'fig').lower().replace(' ', '_')}",
                "content": content,
                "metadata": item
            }
            f.write(json.dumps(chunk_record) + "\n")
            
    print(f"\nVisual anatomy extraction complete! {len(anatomy_records)} records saved to {output_dir}")
    print(f"LightRAG-ready chunk file written to {chunks_file}")

def main():
    parser = argparse.ArgumentParser(description="Extract visual anatomy from AWS A3.0 diagrams")
    parser.add_argument("--figures", nargs="*", help="Specific figure numbers to extract (e.g. B4 B6 B20 B25)")
    parser.add_argument("--backend", choices=["auto", "gemini", "ollama"], default="auto", help="VLM backend")
    args = parser.parse_args()

    process_figures(figures=args.figures, backend=args.backend)

if __name__ == "__main__":
    main()
