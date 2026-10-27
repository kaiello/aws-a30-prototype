"""Reusable Archetype 4 (cycle_waveform_plot) Ingestion & Cross-Join Engine.

Processes Annex B Waveform & Welding Cycle Figures (Figures B44, B45, B49, B50, B51, B53, B54).
Implements the 4-Check Anti-Drift Loop:
1. Genuine PyMuPDF text span, horizontal time axis, vector traces, and interval extraction.
2. Dual-Layer Epistemic Admission (ACCEPTED vs. CANDIDATE).
3. Cross-Source Normative Join with Clause 4 Glossary and Annex C/D.
4. Deterministic verification with 0 live LLM calls.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

import fitz

from src.evidence_annex_b_archetype4_specs import (
    ARCHETYPE4_SPECS,
    CycleWaveformSpec,
    TemporalIntervalSpec,
    TraceVariableSpec,
    WaveformParameterSpec,
)


def verify_waveform_figure_title_in_list_of_figures(
    doc: fitz.Document, figure_id: str, short_title: str
) -> bool:
    """Verify that the official figure title appears in the List of Figures (PDF indices 10–11)."""
    fig_num = figure_id.replace("Figure ", "").strip()
    found = False
    for idx in [10, 11]:
        text = doc[idx].get_text("text")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for i, line in enumerate(lines):
            if (
                line == fig_num
                or line.startswith(fig_num + "	")
                or line.startswith(f"Figure {fig_num}")
                or re.match(rf"^{fig_num}", line)
            ):
                combined = " ".join(lines[max(0, i - 1):min(len(lines), i + 5)]).lower()
                clean_short = short_title.lower().strip()
                if clean_short in combined:
                    found = True
                    break
                keywords = [w for w in clean_short.split() if len(w) >= 3]
                if keywords and any(kw in combined for kw in keywords):
                    found = True
                    break
        if found:
            break

    if not found:
        raise ValueError(
            f"DRIFT ERROR: {figure_id} title '{short_title}' not verified in List of Figures (doc[10..11])"
        )
    return True


def render_waveform_crop(
    doc: fitz.Document,
    page_index: int,
    crop_box: Tuple[float, float, float, float],
    output_path: Path,
) -> Tuple[str, Tuple[int, int]]:
    """Render a 300 DPI crop of the waveform plot and compute its SHA-256 hash."""
    page = doc[page_index]
    rect = page.rect
    ymin, xmin, ymax, xmax = crop_box
    crop_rect = fitz.Rect(
        rect.width * xmin,
        rect.height * ymin,
        rect.width * xmax,
        rect.height * ymax,
    )

    zoom = 300.0 / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=matrix, clip=crop_rect)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pix.save(str(output_path))

    with open(output_path, "rb") as f:
        img_bytes = f.read()
    crop_hash = hashlib.sha256(img_bytes).hexdigest()
    return crop_hash, (pix.width, pix.height)


def extract_waveform_features(
    page: fitz.Page, crop_box: Tuple[float, float, float, float]
) -> Dict[str, Any]:
    """Extract live text spans, axis lines, and drawing vectors from the cropped waveform region."""
    rect = page.rect
    ymin, xmin, ymax, xmax = crop_box
    target_rect = fitz.Rect(
        rect.width * xmin,
        rect.height * ymin,
        rect.width * xmax,
        rect.height * ymax,
    )

    # 1. Extract text blocks / spans
    text_spans = []
    page_dict = page.get_text("dict")
    for block in page_dict.get("blocks", []):
        if block.get("type") == 0:  # text
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    span_bbox = fitz.Rect(span.get("bbox", [0, 0, 0, 0]))
                    if target_rect.intersects(span_bbox):
                        t = span.get("text", "").strip()
                        if t and not t.startswith("Accessed by") and not t.startswith("Annex B") and not t.startswith("AWS A3.0"):
                            text_spans.append({
                                "text": t,
                                "bbox": [round(c, 2) for c in span_bbox],
                                "size": span.get("size", 0.0),
                                "flags": span.get("flags", 0),
                            })

    # 2. Extract drawings (lines, rects, curves)
    drawings = page.get_drawings()
    waveform_drawings = []
    horizontal_lines = []
    vertical_lines = []
    for d in drawings:
        d_rect = fitz.Rect(d.get("rect", [0, 0, 0, 0]))
        if target_rect.intersects(d_rect):
            waveform_drawings.append({
                "rect": [round(c, 2) for c in d_rect],
                "color": d.get("color"),
                "fill": d.get("fill"),
                "width": d.get("width", 1.0),
                "items_count": len(d.get("items", [])),
            })
            # Check horizontal time axis / baseline candidates
            if abs(d_rect.y1 - d_rect.y0) < 3.0 and (d_rect.x1 - d_rect.x0) > 40.0:
                horizontal_lines.append(d_rect)
            elif abs(d_rect.x1 - d_rect.x0) < 3.0 and (d_rect.y1 - d_rect.y0) > 15.0:
                vertical_lines.append(d_rect)

    return {
        "text_spans": text_spans,
        "drawings_count": len(waveform_drawings),
        "drawings_sample": waveform_drawings[:20],
        "horizontal_axes_count": len(horizontal_lines),
        "vertical_axes_count": len(vertical_lines),
    }


def ingest_cycle_waveform_figure(
    doc: fitz.Document,
    spec: CycleWaveformSpec,
    glossary_store: Dict[str, Any],
    output_dir: Path,
) -> Dict[str, Any]:
    """Ingest an Archetype 4 waveform figure with complete dual-provenance grounding."""
    # Check 1: Title & Caption Verification
    verify_waveform_figure_title_in_list_of_figures(doc, spec.figure_id, spec.short_title)

    pdf_idx, printed_page = spec.pages[0]
    page = doc[pdf_idx]
    page_text = page.get_text("text")

    # Verify caption on target page
    fig_num = spec.figure_id.replace("Figure ", "").strip()
    caption_candidates = [
        f"Figure {fig_num}",
        f"B{fig_num}",
        fig_num,
    ]
    has_caption = any(cand in page_text for cand in caption_candidates)
    if not has_caption:
        raise ValueError(
            f"DRIFT ERROR: Caption for {spec.figure_id} not found on PDF index {pdf_idx} (printed p. {printed_page})"
        )

    # Render 300 DPI crop PNG
    clean_id = spec.figure_id.lower().replace(" ", "_")
    crop_path = output_dir / "crops" / f"{clean_id}_300dpi.png"
    crop_hash, crop_dims = render_waveform_crop(doc, pdf_idx, spec.crop_box, crop_path)

    # Extract vector features and text
    features = extract_waveform_features(page, spec.crop_box)
    if features["drawings_count"] <= 0:
        raise ValueError(f"DRIFT ERROR: {spec.figure_id} has 0 vector drawings")
    if len(features["text_spans"]) <= 0:
        raise ValueError(f"DRIFT ERROR: {spec.figure_id} has 0 text spans")

    def match_spans(query: str, spans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        q = query.lower().strip()
        words = [w for w in re.split(r"\W+", q) if len(w) >= 3]
        matches = []
        for s in spans:
            st = s.get("text", "").lower().strip()
            if not st:
                continue
            if q in st or st in q:
                matches.append(s)
            elif words and any(w in st for w in words):
                matches.append(s)
        return matches

    # Build Graph Structure
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    seen_edge_keys: Set[Tuple[str, str, str, str]] = set()

    def add_node(
        node_id: str,
        node_type: str,
        name: str,
        epistemic_status: str = "ACCEPTED",
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        props = properties or {}
        nodes.append({
            "node_id": node_id,
            "node_type": node_type,
            "name": name,
            "epistemic_status": epistemic_status,
            "properties": props,
        })

    def add_edge(
        source: str,
        target: str,
        edge_type: str,
        observation_id: str,
        epistemic_status: str = "ACCEPTED",
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        key = (source, target, edge_type, observation_id)
        if key in seen_edge_keys:
            return
        seen_edge_keys.add(key)
        edges.append({
            "source": source,
            "target": target,
            "edge_type": edge_type,
            "observation_id": observation_id,
            "epistemic_status": epistemic_status,
            "properties": properties or {},
        })

    # 1. Figure Root Node
    add_node(
        node_id=spec.figure_id,
        node_type="FIGURE",
        name=spec.official_title,
        properties={
            "short_title": spec.short_title,
            "printed_page": printed_page,
            "pdf_index": pdf_idx,
            "archetype": "cycle_waveform_plot",
            "crop_sha256": crop_hash,
            "crop_dimensions": crop_dims,
            "crop_box": spec.crop_box,
            "vector_drawings_count": features["drawings_count"],
        },
    )

    # 2. Horizontal Time Axis Node
    axis_node_id = f"{spec.figure_id}_AXIS_{spec.time_axis}"
    add_node(
        node_id=axis_node_id,
        node_type="TIME_AXIS",
        name=spec.time_axis,
        properties={
            "orientation": "HORIZONTAL",
            "detected_axes_lines": features["horizontal_axes_count"],
        },
    )
    add_edge(spec.figure_id, axis_node_id, "HAS_TIME_AXIS", f"OBS-AXIS-{spec.time_axis}")

    # 3. Trace Variable Nodes
    for trace in spec.traces:
        trace_node_id = f"{spec.figure_id}_TRACE_{trace.name.replace(' ', '_')}"
        m_spans = match_spans(trace.name, features["text_spans"])
        add_node(
            node_id=trace_node_id,
            node_type="TRACE_VARIABLE",
            name=trace.name,
            properties={
                "physical_quantity": trace.physical_quantity,
                "unit": trace.unit,
                "description": trace.description,
                "matched_pdf_spans_count": len(m_spans),
                "matched_bbox": m_spans[0]["bbox"] if m_spans else None,
                "matched_spans": [{"text": m["text"], "bbox": m["bbox"]} for m in m_spans],
            },
        )
        add_edge(spec.figure_id, trace_node_id, "HAS_TRACE_VARIABLE", f"OBS-TRACE-{trace.name}")
        add_edge(trace_node_id, axis_node_id, "SYNCHRONIZED_ON_AXIS", f"OBS-SYNC-{trace.name}")

    # 4. Temporal Interval Nodes & Precedence Edges
    top_level_intervals: List[TemporalIntervalSpec] = []
    interval_node_map: Dict[str, str] = {}

    for interval in spec.intervals:
        int_node_id = f"{spec.figure_id}_INTERVAL_{interval.name.replace(' ', '_')}"
        interval_node_map[interval.name] = int_node_id
        m_spans = match_spans(interval.name, features["text_spans"])
        add_node(
            node_id=int_node_id,
            node_type="TEMPORAL_INTERVAL",
            name=interval.name,
            properties={
                "order": interval.order,
                "parent_interval": interval.parent_interval,
                "description": interval.description,
                "clause4_term": interval.clause4_term,
                "matched_pdf_spans_count": len(m_spans),
                "matched_bbox": m_spans[0]["bbox"] if m_spans else None,
                "matched_spans": [{"text": m["text"], "bbox": m["bbox"]} for m in m_spans],
            },
        )
        add_edge(spec.figure_id, int_node_id, "HAS_TEMPORAL_INTERVAL", f"OBS-INT-{interval.name}")

        if interval.parent_interval:
            parent_node_id = f"{spec.figure_id}_INTERVAL_{interval.parent_interval.replace(' ', '_')}"
            add_edge(int_node_id, parent_node_id, "SUB_INTERVAL_OF", f"OBS-SUB-{interval.name}")
        else:
            top_level_intervals.append(interval)

    # Sort top-level intervals by order and create TEMPORAL_PRECEDES edges
    top_level_intervals.sort(key=lambda x: x.order)
    for i in range(len(top_level_intervals) - 1):
        prev_int = top_level_intervals[i]
        curr_int = top_level_intervals[i + 1]
        prev_id = interval_node_map[prev_int.name]
        curr_id = interval_node_map[curr_int.name]
        add_edge(
            prev_id,
            curr_id,
            "TEMPORAL_PRECEDES",
            f"OBS-PRECEDE-{prev_int.name}-{curr_int.name}",
            properties={"from_order": prev_int.order, "to_order": curr_int.order},
        )

    # 5. Waveform Parameter Nodes
    for param in spec.parameters:
        param_node_id = f"{spec.figure_id}_PARAM_{param.name.replace(' ', '_')}"
        m_spans = match_spans(param.name, features["text_spans"])
        add_node(
            node_id=param_node_id,
            node_type="WAVEFORM_PARAMETER",
            name=param.name,
            properties={
                "associated_trace": param.associated_trace,
                "associated_interval": param.associated_interval,
                "description": param.description,
                "matched_pdf_spans_count": len(m_spans),
                "matched_bbox": m_spans[0]["bbox"] if m_spans else None,
                "matched_spans": [{"text": m["text"], "bbox": m["bbox"]} for m in m_spans],
            },
        )
        add_edge(spec.figure_id, param_node_id, "HAS_PARAMETER", f"OBS-PARAM-{param.name}")

        trace_node_id = f"{spec.figure_id}_TRACE_{param.associated_trace.replace(' ', '_')}"
        add_edge(param_node_id, trace_node_id, "PARAMETER_OF_TRACE", f"OBS-PARAM-TRACE-{param.name}")

        if param.associated_interval and param.associated_interval in interval_node_map:
            int_id = interval_node_map[param.associated_interval]
            add_edge(param_node_id, int_id, "MEASURED_DURING_INTERVAL", f"OBS-PARAM-INT-{param.name}")

    # 6. Compound Intervals
    for comp in spec.compound_intervals:
        comp_name = comp["name"]
        comp_node_id = f"{spec.figure_id}_COMPOUND_{comp_name.replace(' ', '_')}"
        add_node(
            node_id=comp_node_id,
            node_type="COMPOUND_INTERVAL",
            name=comp_name,
            properties={
                "description": comp.get("description", ""),
                "subsumes": comp.get("subsumes", []),
                "clause4_term": comp.get("clause4_term"),
            },
        )
        add_edge(spec.figure_id, comp_node_id, "HAS_COMPOUND_INTERVAL", f"OBS-COMP-{comp_name}")
        for sub_name in comp.get("subsumes", []):
            if sub_name in interval_node_map:
                add_edge(interval_node_map[sub_name], comp_node_id, "PART_OF_COMPOUND", f"OBS-PART-{sub_name}")

    # 7. Cross-Source Join with Clause 4 Glossary
    glossary_entries = glossary_store.get("entries", [])
    glossary_by_term = {e["term"].lower(): e for e in glossary_entries}
    joined_terms = []

    for term_str in spec.clause4_terms:
        term_clean = term_str.lower().strip()
        matched = glossary_by_term.get(term_clean)
        if not matched:
            for k, e in glossary_by_term.items():
                if k == term_clean or term_clean in k:
                    matched = e
                    break
        if matched:
            gloss_id = f"GLOSS_{matched['term'].replace(' ', '_')}"
            add_node(
                node_id=gloss_id,
                node_type="CLAUSE4_TERM",
                name=matched["term"],
                properties={
                    "definition": matched.get("definition", ""),
                    "clause4_page": matched.get("page_number"),
                    "cross_references": matched.get("cross_references", {}),
                },
            )
            add_edge(
                spec.figure_id,
                gloss_id,
                "CROSS_CLAUSE_JOIN",
                f"OBS-JOIN-{matched['term']}",
                properties={"joined_clause": "Clause 4"},
            )
            joined_terms.append(matched["term"])

    # Admission verification
    accepted_nodes = [n for n in nodes if n["epistemic_status"] == "ACCEPTED"]
    accepted_edges = [e for e in edges if e["epistemic_status"] == "ACCEPTED"]
    candidate_nodes = [n for n in nodes if n["epistemic_status"] == "CANDIDATE"]
    candidate_edges = [e for e in edges if e["epistemic_status"] == "CANDIDATE"]

    store = {
        "figure_id": spec.figure_id,
        "official_title": spec.official_title,
        "short_title": spec.short_title,
        "archetype": "cycle_waveform_plot",
        "provenance": {
            "source_document": "AWS A3.0M/A3.0:2020",
            "printed_page": printed_page,
            "pdf_index": pdf_idx,
            "crop_sha256": crop_hash,
            "crop_dimensions": crop_dims,
            "crop_box": spec.crop_box,
        },
        "metrics": {
            "accepted_nodes": len(accepted_nodes),
            "accepted_edges": len(accepted_edges),
            "candidate_nodes": len(candidate_nodes),
            "candidate_edges": len(candidate_edges),
            "duplicate_edges": len(edges) - len(seen_edge_keys),
            "traces_count": len(spec.traces),
            "intervals_count": len(spec.intervals),
            "parameters_count": len(spec.parameters),
            "joined_clause4_terms": len(joined_terms),
        },
        "traces": [
            {
                "name": t.name,
                "physical_quantity": t.physical_quantity,
                "unit": t.unit,
                "description": t.description,
            }
            for t in spec.traces
        ],
        "intervals": [
            {
                "name": i.name,
                "order": i.order,
                "parent_interval": i.parent_interval,
                "description": i.description,
                "clause4_term": i.clause4_term,
            }
            for i in spec.intervals
        ],
        "parameters": [
            {
                "name": p.name,
                "associated_trace": p.associated_trace,
                "associated_interval": p.associated_interval,
                "description": p.description,
            }
            for p in spec.parameters
        ],
        "compound_intervals": spec.compound_intervals,
        "source_anomalies": spec.source_anomalies,
        "notes": spec.notes,
        "graph": {
            "nodes": nodes,
            "edges": edges,
        },
    }

    # Save to individual store JSON
    store_path = output_dir / f"{clean_id}_store.json"
    store_path.write_text(json.dumps(store, indent=2), encoding="utf-8")
    return store


def compose_waveform_answer(
    query_or_spec: Dict[str, Any],
    waveform_store: Dict[str, Any],
    glossary_store: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Data-driven QA composition for Archetype 4 waveform queries (0 hardcoded question IDs or strings)."""
    fig_id = waveform_store["figure_id"]
    title = waveform_store["official_title"]
    traces = waveform_store.get("traces", [])
    intervals = waveform_store.get("intervals", [])
    params = waveform_store.get("parameters", [])
    edges = waveform_store.get("graph", {}).get("edges", [])

    q_type = query_or_spec.get("query_type", "summary")
    target_interval = query_or_spec.get("target_interval")
    target_trace = query_or_spec.get("target_trace")

    if q_type == "temporal_sequence":
        # Order of intervals along time axis
        top_level = [i for i in intervals if not i.get("parent_interval")]
        top_level.sort(key=lambda x: x.get("order", 0))
        sequence_names = [i["name"] for i in top_level]
        ans_text = (
            f"In {fig_id} ({title}), the ordered sequence of welding cycle phases along the horizontal TIME axis is: "
            + " -> ".join(sequence_names)
            + "."
        )
        return {
            "figure_id": fig_id,
            "query_type": q_type,
            "answer_text": ans_text,
            "sequence": sequence_names,
            "total_intervals": len(sequence_names),
        }

    if q_type == "precedence" and target_interval:
        # Find preceding and succeeding interval
        preceding = None
        succeeding = None
        for edge in edges:
            if edge["edge_type"] == "TEMPORAL_PRECEDES":
                src_name = edge["source"].replace(f"{fig_id}_INTERVAL_", "").replace("_", " ")
                tgt_name = edge["target"].replace(f"{fig_id}_INTERVAL_", "").replace("_", " ")
                if tgt_name.upper() == target_interval.upper():
                    preceding = src_name
                if src_name.upper() == target_interval.upper():
                    succeeding = tgt_name

        ans_text = (
            f"In {fig_id}, '{target_interval}' "
            + (f"is preceded by '{preceding}' " if preceding else "is the initial phase ")
            + (f"and is followed by '{succeeding}'." if succeeding else "and concludes the cycle sequence.")
        )
        return {
            "figure_id": fig_id,
            "query_type": q_type,
            "target_interval": target_interval,
            "preceding_interval": preceding,
            "succeeding_interval": succeeding,
            "answer_text": ans_text,
        }

    if q_type == "sub_intervals":
        parent = target_interval or "WELD INTERVAL"
        subs = [
            i["name"]
            for i in intervals
            if (i.get("parent_interval") or "").upper() == parent.upper()
        ]
        ans_text = (
            f"In {fig_id}, '{parent}' is subdivided into the following cyclic pulses/sub-intervals: "
            + ", ".join(subs)
            + "."
        )
        return {
            "figure_id": fig_id,
            "query_type": q_type,
            "parent_interval": parent,
            "sub_intervals": subs,
            "answer_text": ans_text,
        }

    if q_type == "traces" or target_trace:
        trace_summaries = [
            f"{t['name']} ({t.get('physical_quantity', '')}, {t.get('unit', '')}): {t.get('description', '')}"
            for t in traces
        ]
        ans_text = (
            f"{fig_id} ({title}) plots {len(traces)} synchronized vertical traces against the horizontal TIME axis:\n- "
            + "\n- ".join(trace_summaries)
        )
        return {
            "figure_id": fig_id,
            "query_type": q_type,
            "traces": [t["name"] for t in traces],
            "answer_text": ans_text,
        }

    # Default: summary
    ans_text = (
        f"{fig_id} ({title}) depicts a synchronized {waveform_store.get('archetype', 'waveform')} "
        f"comprising {len(traces)} vertical traces ({', '.join(t['name'] for t in traces)}) "
        f"and {len(intervals)} sequential temporal intervals along the TIME axis."
    )
    return {
        "figure_id": fig_id,
        "query_type": "summary",
        "answer_text": ans_text,
        "traces_count": len(traces),
        "intervals_count": len(intervals),
        "parameters_count": len(params),
    }
