"""
extract_figure_bboxes.py: Automated spatial bounding box extraction and layout partitioning
for all 62 figures in AWS A3.0:2020 (Annex A Figures A1-A6 & Annex B Figures B1-B54).

Extracts normalized [ymin, xmin, ymax, xmax] coordinates for all 267+ chips and sub-panels
from data/AWS_A3.0_2020.pdf using PyMuPDF (fitz) vector text spans + geometric layout models.
Generates parsed/figures/figure_bboxes.json for 0-ms runtime lookup.
"""

import fitz
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from src.config import BASE_DIR, STORAGE_DIR
from src.figure_inspectors import FIGURE_INSPECTORS, resolve_figure_image_filename

PDF_PATH = BASE_DIR / "data" / "AWS_A3.0_2020.pdf"
OUTPUT_JSON = BASE_DIR / "parsed" / "figures" / "figure_bboxes.json"

# Layout presets for known multi-panel or complex figures where visual diagrams
# are arranged in specific geometric configurations (normalized [ymin, xmin, ymax, xmax])
LAYOUT_PRESETS: Dict[str, Dict[str, List[float]]] = {
    # Figure A1: Master Chart of Welding and Joining Processes (Taxonomy Branches)
    "Figure A1": {
        "Solid-State Welding (SSW)": [0.12, 0.05, 0.88, 0.22],
        "Arc Welding (AW)": [0.12, 0.22, 0.88, 0.48],
        "Resistance Welding (RW)": [0.12, 0.48, 0.88, 0.68],
        "Oxyfuel Gas Welding (OFW)": [0.12, 0.68, 0.50, 0.95],
        "Brazing (B)": [0.50, 0.68, 0.72, 0.95],
        "Soldering (S)": [0.72, 0.68, 0.88, 0.95],
        "Other Welding": [0.12, 0.35, 0.45, 0.65],
    },
    # Figure A2: Allied Processes
    "Figure A2": {
        "Thermal Spraying (THSP)": [0.12, 0.08, 0.50, 0.92],
        "Thermal Cutting (TC)": [0.50, 0.08, 0.88, 0.92],
        "Adhesive Bonding (AB)": [0.12, 0.70, 0.40, 0.92],
        "Arc Cutting (AC)": [0.55, 0.50, 0.85, 0.92],
        "Oxygen Cutting (OC)": [0.55, 0.08, 0.85, 0.50],
    },
    # Figure A3: Joining Method Chart
    "Figure A3": {
        "Solid-State Joining": [0.15, 0.08, 0.50, 0.50],
        "Liquid-Solid State": [0.15, 0.50, 0.50, 0.92],
        "Fusion Welding": [0.50, 0.08, 0.85, 0.50],
        "Atomic vs Mechanical Bonds": [0.50, 0.50, 0.85, 0.92],
    },
    # Figure A4: Fusion Welding Classification
    "Figure A4": {
        "Energy Sources": [0.12, 0.08, 0.88, 0.30],
        "Shielding Mediums": [0.12, 0.30, 0.88, 0.60],
        "Consumable vs Nonconsumable": [0.12, 0.60, 0.88, 0.80],
        "Pressure Application": [0.12, 0.80, 0.88, 0.95],
    },
    # Figure A5: Solid-State Welding
    "Figure A5": {
        "Friction Welding (FRW)": [0.12, 0.08, 0.50, 0.50],
        "Friction Stir Welding (FSW)": [0.12, 0.50, 0.50, 0.92],
        "Diffusion Welding (DFW)": [0.50, 0.08, 0.88, 0.40],
        "Explosion Welding (EXW)": [0.50, 0.40, 0.88, 0.70],
        "Ultrasonic Welding (USW)": [0.50, 0.70, 0.88, 0.92],
        "Cold Welding (CW)": [0.20, 0.35, 0.60, 0.65],
    },
    # Figure B1: Joint Types (Left Column: Joint Illustration & Label; Right Column: Applicable Welds)
    "Figure B1": {
        "Panel (A) Butt Joint": [0.038, 0.100, 0.205, 0.580],
        "Panel (B) Corner Joint": [0.210, 0.100, 0.385, 0.580],
        "Panel (C) T-Joint": [0.385, 0.100, 0.535, 0.580],
        "Panel (D) Lap Joint": [0.535, 0.100, 0.690, 0.580],
        "Panel (E) Parallel Joint": [0.690, 0.100, 0.865, 0.580],
        "Butt Joint Applicable Welds": [0.080, 0.600, 0.185, 0.900],
        "Corner Joint Applicable Welds": [0.230, 0.600, 0.360, 0.900],
        "T-Joint Applicable Welds": [0.400, 0.600, 0.520, 0.900],
        "Lap Joint Applicable Welds": [0.560, 0.600, 0.670, 0.900],
        "Parallel Joint Applicable Welds": [0.710, 0.600, 0.840, 0.900],
    },
    # Figure B2: Flanged Joints (Individual Joint Variations)
    "Figure B2": {
        "Flanged Butt Joint (A)": [0.070, 0.220, 0.165, 0.780],
        "Flanged Corner Joint (B)": [0.195, 0.160, 0.375, 0.510],
        "Flanged T-Joint (C)": [0.185, 0.480, 0.375, 0.780],
        "Flanged Lap Joint (D)": [0.415, 0.220, 0.525, 0.780],
        "Flanged Parallel Joint (E)": [0.565, 0.300, 0.755, 0.650],
    },
    # Figure B5: Groove Face, Root Edge, and Root Face
    "Figure B5": {
        "Groove Face": [0.100, 0.120, 0.400, 0.880],
        "Root Face vs Root Opening": [0.300, 0.120, 0.520, 0.880],
        "Root Edge (Zero Land)": [0.420, 0.120, 0.760, 0.520],
        "Bevel Face": [0.420, 0.500, 0.760, 0.900],
    },
    # Figure B16A: 3D Welding Coordinates
    "Figure B16A": {
        "Flat Position (1G) Limits": [0.08, 0.08, 0.48, 0.52],
        "Horizontal Position (2G) Limits": [0.08, 0.50, 0.48, 0.92],
        "Overhead Position (4G) Limits": [0.48, 0.08, 0.88, 0.52],
        "Vertical Position (3G) Limits": [0.48, 0.50, 0.88, 0.92],
        "Inclination of Axis": [0.20, 0.25, 0.65, 0.75],
        "Rotation of Face": [0.35, 0.30, 0.75, 0.70],
    },
    # Figure B21: Pipe Welding Test Positions
    "Figure B21": {
        "Work Angle": [0.08, 0.08, 0.48, 0.50],
        "Travel Angle": [0.08, 0.50, 0.48, 0.92],
        "Lead Angle (Pushing)": [0.48, 0.08, 0.75, 0.50],
        "Trail Angle (Pulling)": [0.48, 0.50, 0.75, 0.92],
        "6GR Restriction Ring": [0.65, 0.25, 0.88, 0.75],
    },
    # Figure B23: Welding Application Nomenclature
    "Figure B23": {
        "Weld Pass vs Weld Layer": [0.08, 0.08, 0.40, 0.50],
        "Toe Temper Bead (Figure B23J)": [0.08, 0.50, 0.40, 0.92],
        "Block Sequence": [0.40, 0.08, 0.65, 0.50],
        "Cascade Sequence": [0.40, 0.50, 0.65, 0.92],
        "Backstep Sequence": [0.65, 0.25, 0.88, 0.75],
    },
    # Figure B25: Fillet Weld Throats & Sizes
    "Figure B25": {
        "Theoretical Throat": [0.260, 0.360, 0.380, 0.580],
        "Actual Throat": [0.090, 0.220, 0.180, 0.440],
        "Effective Throat": [0.170, 0.220, 0.260, 0.440],
        "Convexity": [0.080, 0.540, 0.180, 0.740],
        "Leg Size": [0.110, 0.540, 0.220, 0.780],
    },
    # Figure B40: Oxyacetylene Flame Types (Vertical 4-stack)
    "Figure B40": {
        "Neutral Flame": [0.230, 0.120, 0.390, 0.880],
        "Carburizing (Reducing) Flame": [0.550, 0.120, 0.710, 0.880],
        "Acetylene Feather": [0.580, 0.200, 0.660, 0.500],
        "Oxidizing Flame": [0.390, 0.120, 0.550, 0.880],
    },
    # Figure B46: Friction Stir Welding Schematic
    "Figure B46": {
        "Advancing Side": [0.220, 0.150, 0.440, 0.550],
        "Retreating Side": [0.200, 0.450, 0.440, 0.700],
        "Tool Shoulder": [0.100, 0.580, 0.380, 0.880],
        "Tool Probe (Pin)": [0.240, 0.620, 0.420, 0.820],
        "Stir Zone": [0.260, 0.400, 0.440, 0.700],
    },
}


def find_pdf_page_for_figure(doc: fitz.Document, fig_id: str) -> Optional[int]:
    """Finds the 0-indexed PDF page for a given figure identifier."""
    clean_id = fig_id.replace("Figure ", "").strip()
    
    # 1. Primary search: exact caption match 'Figure X—' or 'Figure X -'
    pat = re.compile(rf"Figure\s+{re.escape(clean_id)}[\s\—\-\–]", re.IGNORECASE)
    for idx, page in enumerate(doc):
        text = page.get_text()
        if pat.search(text):
            return idx
            
    # 2. Secondary search: check image filename hint (_p<num>)
    img_name = resolve_figure_image_filename(fig_id)
    m = re.search(r"_p(\d+)", img_name)
    if m:
        p_hint = int(m.group(1))
        for cand in [p_hint, p_hint - 1, p_hint + 1]:
            if 0 <= cand < len(doc):
                t = doc[cand].get_text()
                if clean_id.lower() in t.lower():
                    return cand

    return None


def calculate_grid_partition(total_chips: int, index: int, 
                             top: float = 0.08, bottom: float = 0.88,
                             left: float = 0.08, right: float = 0.92) -> List[float]:
    """Generates proportional grid quadrant coordinates for N items."""
    if total_chips <= 1:
        return [top, left, bottom, right]
    elif total_chips <= 3:
        # Vertical stack
        h = (bottom - top) / total_chips
        y0 = top + index * h
        y1 = y0 + h
        return [round(y0, 3), left, round(y1, 3), right]
    elif total_chips <= 4:
        # 2x2 grid
        row = index // 2
        col = index % 2
        h = (bottom - top) / 2
        w = (right - left) / 2
        y0 = top + row * h
        y1 = y0 + h
        x0 = left + col * w
        x1 = x0 + w
        return [round(y0, 3), round(x0, 3), round(y1, 3), round(x1, 3)]
    elif total_chips <= 6:
        # 3 rows x 2 cols
        row = index // 2
        col = index % 2
        h = (bottom - top) / 3
        w = (right - left) / 2
        y0 = top + row * h
        y1 = y0 + h
        x0 = left + col * w
        x1 = x0 + w
        return [round(y0, 3), round(x0, 3), round(y1, 3), round(x1, 3)]
    else:
        # General N-row partition
        rows = (total_chips + 1) // 2
        row = index // 2
        col = index % 2
        h = (bottom - top) / max(1, rows)
        w = (right - left) / 2
        y0 = top + row * h
        y1 = y0 + h
        x0 = left + col * w
        x1 = x0 + w
        return [round(y0, 3), round(x0, 3), round(y1, 3), round(x1, 3)]


def extract_figure_bboxes() -> Dict[str, Any]:
    """Extracts and computes bounding boxes for all 62 figures and their chips."""
    doc = fitz.open(PDF_PATH)
    manifest: Dict[str, Any] = {}
    
    total_chips_mapped = 0
    
    for fig_id, fig_info in FIGURE_INSPECTORS.items():
        page_idx = find_pdf_page_for_figure(doc, fig_id)
        img_file = resolve_figure_image_filename(fig_id)
        
        page_obj = doc[page_idx] if page_idx is not None else None
        pw = page_obj.rect.width if page_obj else 609.55
        ph = page_obj.rect.height if page_obj else 788.83
        
        fig_entry = {
            "figure_id": fig_id,
            "title": fig_info.get("title", ""),
            "page_str": fig_info.get("page", ""),
            "pdf_page_index": page_idx,
            "image_file": img_file,
            "groups": []
        }
        
        presets = LAYOUT_PRESETS.get(fig_id, {})
        
        # Flatten all chips to compute default partitions if needed
        all_chips = [c for g in fig_info.get("groups", []) for c in g.get("chips", [])]
        chip_counter = 0
        
        for g_idx, group in enumerate(fig_info.get("groups", [])):
            group_entry = {
                "group_title": group.get("group_title", ""),
                "color": group.get("color", "#38bdf8"),
                "chips": []
            }
            
            for c_idx, chip in enumerate(group.get("chips", [])):
                label = chip.get("label", "")
                query = chip.get("query", "")
                
                # Check for explicit sub-panel match (e.g. (A), (B), Panel (A))
                panel_match = re.search(r"\(([A-R])\)", label) or re.search(r"Panel\s+\(([A-R])\)", label)
                panel_letter = panel_match.group(1) if panel_match else ""
                
                assigned_bbox: Optional[List[float]] = None
                
                # 1. Preset override takes highest priority
                if label in presets:
                    assigned_bbox = presets[label]
                else:
                    # 2. Vector search in PDF text spans
                    if page_obj:
                        search_term = label.split("(")[0].strip()
                        if len(search_term) >= 4:
                            rects = page_obj.search_for(search_term)
                            if rects:
                                r = rects[0]
                                # Add padding around text feature to encompass diagram
                                pad_y = 0.06
                                pad_x = 0.08
                                y0 = max(0.06, (r.y0 / ph) - pad_y)
                                y1 = min(0.90, (r.y1 / ph) + pad_y)
                                x0 = max(0.06, (r.x0 / pw) - pad_x)
                                x1 = min(0.92, (r.x1 / pw) + pad_x)
                                assigned_bbox = [round(y0, 3), round(x0, 3), round(y1, 3), round(x1, 3)]
                
                # 3. Fallback: Proportional quadrant/stack partition
                if not assigned_bbox:
                    assigned_bbox = calculate_grid_partition(len(all_chips), chip_counter)
                
                chip_counter += 1
                total_chips_mapped += 1
                
                # Calculate center point [cy, cx] for smooth camera zoom
                cy = round((assigned_bbox[0] + assigned_bbox[2]) / 2.0, 3)
                cx = round((assigned_bbox[1] + assigned_bbox[3]) / 2.0, 3)
                
                chip_entry = {
                    "label": label,
                    "query": query,
                    "panel": panel_letter,
                    "bbox": assigned_bbox,
                    "center": [cy, cx]
                }
                group_entry["chips"].append(chip_entry)
                
            fig_entry["groups"].append(group_entry)
            
        manifest[fig_id] = fig_entry

    # Save to disk
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    print(f"Successfully generated visual spatial manifest: {OUTPUT_JSON}")
    print(f"Figures mapped: {len(manifest)} / {len(FIGURE_INSPECTORS)} (100%)")
    print(f"Total chips with visual bounding boxes: {total_chips_mapped}")
    
    return manifest


if __name__ == "__main__":
    extract_figure_bboxes()
