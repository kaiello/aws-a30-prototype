"""Opt-in Figure A2 source adapter over the existing chart and SQLite core.

Native rectangles/line segments and two retained local OCR readings are inputs.
No source process names, designations, relationship answers or QA keys live here.
Acceptance is limited to literal/physical observations, never semantic subtype.
"""
from __future__ import annotations

import argparse
from collections import deque
from copy import deepcopy
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import re
import statistics
import time

from src.evidence_a1_cli import write_private_output
from src.evidence_a1_raster import _run_tesseract, _engine_version, _words_from_tsv, _rows, _designation

VERSION = "a2-source-aware-ingest-1.4"
ELEMENT = "Figure A2"
REGION = [.075, .10, .45, .89]
DPI = 300
MIN_CONFIDENCE = 80.0


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _digest(value):
    return _sha(_json(value).encode())


def _literal(value):
    return " ".join(re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", value.casefold()))


def _private(root, path, *, suffix=None):
    root = Path(root).resolve(strict=True)
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate
    for item in (candidate, *candidate.parents):
        if item == root:
            break
        if item.is_symlink() or getattr(item, "is_junction", lambda: False)():
            raise ValueError("A2_LINKED_PRIVATE_PATH")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root / "storage/evidence_v2") or (suffix and resolved.suffix != suffix):
        raise ValueError("A2_PRIVATE_PATH_INVALID")
    return resolved


def _source(root):
    """Authenticate the canonical document and declared A2 page before rendering."""
    import fitz
    root = Path(root).resolve(strict=True)
    manifest_path = root / "config/aws_a30_2020_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    document = manifest["document"]
    figure = next(item for item in manifest["figures"] if item["id"] == "figure:figure_a2")
    anchor = figure["anchors"][0]
    if (figure["label"] != ELEMENT or len(figure["anchors"]) != 1 or anchor["pdf_index"] != 88
            or str(anchor["printed_label"]) != "76"):
        raise ValueError("A2_SOURCE_LOCATOR_MISMATCH")
    source_path, asset_path = root / document["pdf_relpath"], root / figure["assets"][0]["relpath"]
    if (not source_path.resolve().is_relative_to(root) or not asset_path.resolve().is_relative_to(root)
            or source_path.is_symlink() or asset_path.is_symlink()):
        raise ValueError("A2_SOURCE_PATH_INVALID")
    source_hash, asset_hash = _sha(source_path.read_bytes()), _sha(asset_path.read_bytes())
    if source_hash != document["sha256"] or asset_hash != figure["assets"][0]["sha256"]:
        raise ValueError("A2_SOURCE_BYTES_CHANGED")
    with fitz.open(source_path) as pdf:
        page = pdf[anchor["pdf_index"]]
        bounds = fitz.Rect(REGION[1]*page.rect.width, REGION[0]*page.rect.height,
                           REGION[3]*page.rect.width, REGION[2]*page.rect.height)
        captions = [block for block in page.get_text("blocks") if re.search(r"Figure\s+A2\b", block[4])]
        if len(captions) != 1 or captions[0][1] <= bounds.y1:
            raise ValueError("A2_FIGURE_SCOPE_NOT_ESTABLISHED")
        drawings = page.get_drawings()
        rectangles, lines = [], []
        for ordinal, drawing in enumerate(drawings):
            items = drawing["items"]
            if len(items) == 1 and items[0][0] == "re" and "s" in drawing["type"]:
                rectangle = fitz.Rect(items[0][1])
                if bounds.contains(rectangle) and rectangle.width >= 40 and rectangle.height >= 15:
                    if not any(max(abs(a-b) for a,b in zip(rectangle, item["pdf_bbox"])) < .1 for item in rectangles):
                        rectangles.append({"pdf_bbox": list(rectangle), "drawing_ordinal": ordinal})
            if "s" in drawing["type"]:
                for item_index, item in enumerate(items):
                    if item[0] == "l" and bounds.contains(item[1]) and bounds.contains(item[2]):
                        lines.append({"pdf_endpoints": [list(item[1]), list(item[2])],
                                      "drawing_ordinal": ordinal, "item_index": item_index})
        pixmap = page.get_pixmap(matrix=fitz.Matrix(DPI/72, DPI/72), clip=bounds, alpha=False)
        image = pixmap.tobytes("png")
        geometry = {"page_size": [page.rect.width, page.rect.height], "region": REGION,
            "pixel_origin": [pixmap.x, pixmap.y], "pixel_size": [pixmap.width, pixmap.height],
            "dpi": DPI, "rectangles": sorted(rectangles, key=lambda item: (item["pdf_bbox"][1], item["pdf_bbox"][0])),
            "lines": lines, "caption": captions[0][4].strip(),
            "native_text_inside_region": page.get_text("text", clip=bounds)}
    edition = document["standard_id"] + "@" + str(document["edition"])
    source_id = "source:" + _digest([edition, source_hash])
    locator = {"element_id": ELEMENT, "canonical_element_id": figure["id"],
        "source_identity_id": source_id, "pdf_index": anchor["pdf_index"],
        "printed_page": str(anchor["printed_label"]), "order": 0,
        "region_scope": "figure_region", "region": REGION}
    source = {"edition_id": edition, "source_identity_id": source_id, "locator": locator,
        "source_pdf_sha256": source_hash, "manifest_sha256": _sha(manifest_path.read_bytes()),
        "manifest_asset_sha256": asset_hash, "title": figure["title"],
        "source_pdf_relpath": document["pdf_relpath"], "asset_relpath": figure["assets"][0]["relpath"]}
    return source, geometry, image


def _pixel_box(pdf_box, geometry):
    scale, (ox, oy) = geometry["dpi"]/72, geometry["pixel_origin"]
    x0,y0,x1,y1 = pdf_box
    return [round(x0*scale-ox), round(y0*scale-oy), round((x1-x0)*scale), round((y1-y0)*scale)]


def _page_region(pixel_box, geometry):
    x,y,w,h = pixel_box
    scale, (ox, oy) = geometry["dpi"]/72, geometry["pixel_origin"]
    width,height = geometry["page_size"]
    return [round((y+oy)/scale/height, 8), round((x+ox)/scale/width, 8),
            round((y+h+oy)/scale/height, 8), round((x+w+ox)/scale/width, 8)]


def _inside(box, child, margin=0):
    x,y,w,h = box
    a,b,c,d = child
    return x-margin <= a and y-margin <= b and a+c <= x+w+margin and b+d <= y+h+margin


def _combine(rows):
    return " ".join(row["text"] for row in rows)


def _heading_rows(rows):
    headers = []
    for row in rows:
        letters = "".join(re.findall(r"[A-Za-z]", row["text"]))
        if letters and letters.isupper():
            headers.append(row)
        else:
            break
    return headers


def _row_fields(row, box, column_x=None):
    # Keep the raw reading unchanged; a punctuation-only OCR speck cannot
    # collapse the observed name/right-column gap into an invented label.
    words = [word for word in row["words"] if re.search(r"[A-Za-z0-9]",word["text"])]
    parsed = _designation({**row,"words":words,"text":" ".join(word["text"] for word in words)},box)
    if parsed[1] is None and column_x is not None and len(words)>1:
        last = words[-1]
        # A long observed name can approach the code column more closely than
        # A1's gap heuristic. Require alignment with other observed row codes.
        if (re.fullmatch(r"[A-Z][A-Z0-9-]*",last["text"])
                and abs(last["pixel_bbox"][0]-column_x)<=max(3,last["pixel_bbox"][3]*.4)
                and last["pixel_bbox"][0]>=box[0]+box[2]*.65):
            return " ".join(word["text"] for word in words[:-1]),last["text"],"observed_right_column_alignment"
    return parsed


def _union(boxes):
    x0,y0 = min(box[0] for box in boxes), min(box[1] for box in boxes)
    x1,y1 = max(box[0]+box[2] for box in boxes), max(box[1]+box[3] for box in boxes)
    return [x0,y0,x1-x0,y1-y0]


def _offset_words(tsv, width, height, offset=(0, 0)):
    words,rejected = _words_from_tsv(tsv, width, height)
    if rejected:
        raise ValueError("A2_OCR_GEOMETRY_INVALID")
    for word in words:
        word["pixel_bbox"][0] += offset[0]
        word["pixel_bbox"][1] += offset[1]
    return words


def _ink_support(ink, words):
    fractions = []
    for word in words:
        x,y,w,h = word["pixel_bbox"]
        patch = ink[y:y+h, x:x+w]
        fractions.append(float((patch > 0).mean()) if patch.size else 0.0)
    return bool(fractions) and all(.02 < fraction < .90 for fraction in fractions)


def _uncovered_text_bands(ink, box, rows):
    """Account for body ink without using an expected process-count reference."""
    import cv2
    import numpy as np
    x,y,w,h = box
    local = ink[y+5:y+h-5, x+5:x+w-5].copy()
    if not local.size:
        return [[y,y+h]]
    line = cv2.morphologyEx(local, cv2.MORPH_OPEN,
                           cv2.getStructuringElement(cv2.MORPH_RECT, (max(20,w//2),1)))
    local = cv2.bitwise_and(local, cv2.bitwise_not(line))
    occupied = np.count_nonzero(local,axis=1) >= 3
    bands, start = [], None
    for index, value in enumerate([*occupied.tolist(), False]):
        if value and start is None:
            start = index
        if not value and start is not None:
            if index-start >= 2:
                top,bottom = y+5+start,y+5+index
                if not any(row["pixel_bbox"][1]-4 <= (top+bottom)/2 <= row["pixel_bbox"][1]+row["pixel_bbox"][3]+4 for row in rows):
                    bands.append([top,bottom])
            start = None
    return bands


def _line_interval(endpoints, box):
    """Liang–Barsky interval where a native segment intersects a rectangle."""
    (x0,y0),(x1,y1) = endpoints
    dx,dy = x1-x0,y1-y0
    a,b,c,d = box
    low,high = 0.0,1.0
    for p,q in [(-dx,x0-a),(dx,a+c-x0),(-dy,y0-b),(dy,b+d-y0)]:
        if abs(p) < 1e-12:
            if q < 0:
                return None
        elif p < 0:
            low = max(low,q/p)
        else:
            high = min(high,q/p)
        if low > high:
            return None
    return (low, high)


def _chart_closure(ink, groups, primary, connectors):
    """Account for crop ink outside actual words, borders and connector strokes."""
    import cv2
    import numpy as np
    residual = ink.copy()
    word_counts = {}
    for group in groups:
        for row in group["rows"]:
            for word in row["words"]:
                key = word["tsv_row_index"]
                word_counts[key] = word_counts.get(key,0)+1
                x,y,w,h = word["pixel_bbox"]
                residual[max(0,y-2):y+h+2,max(0,x-2):x+w+2] = 0
        x,y,w,h = group["box"]
        cv2.rectangle(residual,(x,y),(x+w,y+h),0,10)
        # A corroborating reading may locate a recognized heading word more
        # accurately (e.g. the first reading clips its last glyph). Match actual
        # words, not full heading spans, before accounting for those anchors.
        heading_words = [word for row in group["headers"] for word in row["words"]]
        for row in group.get("other_headers",[]):
            for word in row["words"]:
                matches = [original for original in heading_words if _literal(original["text"])==_literal(word["text"])
                    and abs((original["pixel_bbox"][1]+original["pixel_bbox"][3]/2)
                            -(word["pixel_bbox"][1]+word["pixel_bbox"][3]/2)) <= max(original["pixel_bbox"][3],word["pixel_bbox"][3])]
                if len(matches)==1:
                    x,y,w,h = word["pixel_bbox"]
                    residual[max(0,y-2):y+h+2,max(0,x-2):x+w+2] = 0
                    heading_words.append(word)
        # Detect actual horizontal underline ink across the baseline (including
        # spaces), rather than clearing its rectangular union or word gaps.
        for row in group["headers"]:
            x,y,w,h = row["pixel_bbox"]
            top = max(0,min(word["pixel_bbox"][1]+word["pixel_bbox"][3]-4 for word in row["words"]))
            bottom = min(ink.shape[0],y+h+7)
            left,right = max(0,x-6),min(ink.shape[1],x+w+6)
            patch = ink[top:bottom,left:right]
            decoration = cv2.morphologyEx(patch,cv2.MORPH_OPEN,
                cv2.getStructuringElement(cv2.MORPH_RECT,(max(20,min(word["pixel_bbox"][2] for word in row["words"])//2),1)))
            decoration = cv2.dilate(decoration,np.ones((3,1),dtype=np.uint8))
            residual[top:bottom,left:right][decoration>0] = 0
    for connector in connectors:
        if connector["verified"]:
            endpoints = np.rint(connector["pixel_endpoints"]).astype("int32")
            thickness = math.ceil(connector["observed_stroke_width_pixels"])+2
            cv2.line(residual,tuple(endpoints[0]),tuple(endpoints[1]),0,thickness)
    count,_,stats,_ = cv2.connectedComponentsWithStats(residual,8)
    unexplained = [[int(value) for value in item] for item in stats[1:count] if item[4]>=4]
    orphans = [word["tsv_row_index"] for word in primary if word_counts.get(word["tsv_row_index"])!=1]
    return {"complete":not unexplained and not orphans,"unexplained_ink_components":unexplained,
        "orphan_or_duplicate_word_ids":orphans,
        "scope":"entire_selected_A2_crop","criterion":"individual_word_anchors_native_borders_and_verified_connector_strokes_only",
        "qualification":"No expected label/row totals used; residual text is not silently masked by full body-row spans."}


def _physical_connectors(geometry, box_nodes, ink):
    """Clip native lines at adjacent box boundaries, then verify actual ink."""
    import cv2
    import numpy as np
    scale, (ox,oy) = geometry["dpi"]/72,geometry["pixel_origin"]
    near = cv2.dilate(ink, np.ones((5,5),np.uint8)) > 0
    results = {}
    for line in geometry["lines"]:
        endpoints = [[x*scale-ox,y*scale-oy] for x,y in line["pdf_endpoints"]]
        contacts = sorted((interval[0],interval[1],identifier) for identifier,box in box_nodes.items()
            if (interval := _line_interval(endpoints,box)) is not None)
        for left,right in zip(contacts,contacts[1:]):
            if right[0] <= left[1] + 1e-6:
                continue
            a,b = np.array(endpoints[0]),np.array(endpoints[1])
            first,last = a+(b-a)*left[1],a+(b-a)*right[0]
            samples = np.linspace(first,last,max(2,int(np.linalg.norm(last-first)*2)))
            pixels = np.rint(samples).astype(int)
            valid = ((pixels[:,0]>=0)&(pixels[:,0]<ink.shape[1])&(pixels[:,1]>=0)&(pixels[:,1]<ink.shape[0]))
            support = near[pixels[valid,1],pixels[valid,0]]
            fraction = float(support.mean()) if support.size else 0.0
            verified = bool(valid.all() and fraction >= .97)
            lower = np.maximum(0,np.minimum(first,last)-4)
            upper = np.minimum([ink.shape[1],ink.shape[0]],np.maximum(first,last)+4)
            key = tuple(sorted([left[2],right[2]]))
            normal = np.array([-(last-first)[1],(last-first)[0]])/np.linalg.norm(last-first)
            widths = []
            for position_fraction in np.linspace(.1,.9,17):
                center = first+(last-first)*position_fraction
                offsets = np.arange(-20,21)
                ray = np.rint(center+offsets[:,None]*normal).astype(int)
                inside = ((ray[:,0]>=0)&(ray[:,0]<ink.shape[1])&(ray[:,1]>=0)&(ray[:,1]<ink.shape[0]))
                occupied = np.zeros(41,dtype=bool)
                occupied[inside] = ink[ray[inside,1],ray[inside,0]]>0
                middle = [i for i in range(17,24) if occupied[i]]
                if not middle:
                    continue
                selected = min(middle,key=lambda i:abs(i-20));low=high=selected
                while low>0 and occupied[low-1]:low-=1
                while high<40 and occupied[high+1]:high+=1
                widths.append(high-low+1)
            stroke_width = float(np.percentile(widths,95)) if widths else 0.0
            record = {"end_ids": list(key), "verified": verified and stroke_width>0, "direction": "undirected",
                "pixel_endpoints": [first.tolist(),last.tolist()],
                "region": _page_region([*lower,*(upper-lower)],geometry),
                "native_drawing_ordinal": line["drawing_ordinal"],"native_item_index":line["item_index"],
                "ink_coverage": fraction, "observed_stroke_width_pixels":stroke_width,
                "criterion": "adjacent_native_box_contacts_and_97_percent_visible_pixel_stroke",
                "qualification": "Physical connection only; direction for navigation is not a printed arrow or semantic subtype."}
            if key not in results or record["ink_coverage"] > results[key]["ink_coverage"]:
                results[key] = record
    return list(results.values())


def _assemble(seed, image_bytes, artifacts):
    """Recompute a source-scoped candidate graph and its per-predicate checks."""
    import cv2
    import numpy as np
    geometry,source = seed["geometry"],seed["source"]
    image = cv2.imdecode(np.frombuffer(image_bytes,dtype=np.uint8),cv2.IMREAD_GRAYSCALE)
    if image is None or [image.shape[1],image.shape[0]] != geometry["pixel_size"]:
        raise ValueError("A2_IMAGE_DIMENSIONS_INVALID")
    ink = cv2.threshold(image,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]
    image_hash = _sha(image_bytes)
    width,height = geometry["pixel_size"]
    primary = _offset_words(seed["primary_ocr"]["tsv"],width,height)
    groups = []
    for index, rectangle in enumerate(geometry["rectangles"]):
        box = _pixel_box(rectangle["pdf_bbox"],geometry)
        words = [word for word in primary if _inside(box,word["pixel_bbox"],2)]
        rows = _rows(words)
        secondary = seed["secondary_ocr"][index]
        if secondary["box_index"] != index or secondary["pixel_bbox"] != box:
            raise ValueError("A2_SECONDARY_SCOPE_MISMATCH")
        patch = secondary["patch_bbox"]
        other_words = _offset_words(secondary["tsv"],patch[2],patch[3],patch[:2])
        other_rows = _rows(other_words)
        headers,other_headers = _heading_rows(rows),_heading_rows(other_rows)
        if not headers:
            raise ValueError("A2_HEADING_UNRESOLVED")
        heading = _combine(headers).strip(" _")
        identifier = "a2box:"+_digest([image_hash,rectangle["pdf_bbox"]])[:24]
        groups.append({"id": identifier,"box":box,"rows":rows,"headers":headers,
            "other_rows":other_rows,"other_headers":other_headers,"heading":heading,
            "header_supported": _literal(heading)==_literal(_combine(other_headers))
                and min(word["confidence"] for row in headers+other_headers for word in row["words"]) >= MIN_CONFIDENCE
                and _ink_support(ink,[word for row in headers for word in row["words"]])})
    caption_words = set(_literal(source["title"]).split()) - {"master","chart","of","the"}
    scores = [(len(caption_words & set(_literal(group["heading"]).split())), group) for group in groups]
    best = max((score for score,_ in scores),default=0)
    roots = [group for score,group in scores if score==best and score>0]
    if len(roots) != 1:
        raise ValueError("A2_ROOT_CAPTION_MATCH_AMBIGUOUS")
    root = roots[0]
    nodes,edges,decisions,coverage,enclosures = [],[],{},{},{}
    box_nodes = {}
    node_group = {}
    for group in groups:
        box_nodes[group["id"]] = group["box"]
        node = {"id":group["id"],"kind":"root" if group is root else "category", "label":group["heading"],
            "region": _page_region(group["box"],geometry),
            "literal_region": _page_region(_union([row["pixel_bbox"] for row in group["headers"]]),geometry)}
        nodes.append(node);node_group[node["id"]] = group
        heading_code = re.search(r"\(([A-Z][A-Z0-9-]*)\)\s*$",node["label"])
        if heading_code:
            node["code"] = heading_code[1]
        decisions[node["id"]] = {"label_supported":bool(group["header_supported"]),
            "designation_supported":bool(group["header_supported"] and heading_code),
            "criterion":"two_local_ocr_readings_agree_above_80_confidence_and_visible_ink",
            "native_rectangle_pdf_bbox": geometry["rectangles"][groups.index(group)]["pdf_bbox"]}
        body = group["rows"][len(group["headers"]):]
        columns = [row["words"][-1]["pixel_bbox"][0] for row in body if _row_fields(row,group["box"])[1]]
        column_x = statistics.median(columns) if len(columns)>=2 else None
        processes = []
        for row in body:
            label,code,method = _row_fields(row,group["box"],column_x)
            other = [candidate for candidate in group["other_rows"][len(group["other_headers"]):]
                if abs((candidate["pixel_bbox"][1]+candidate["pixel_bbox"][3]/2)-(row["pixel_bbox"][1]+row["pixel_bbox"][3]/2)) <= max(row["pixel_bbox"][3],candidate["pixel_bbox"][3])*.65]
            paired = [_row_fields(candidate,group["box"],column_x) for candidate in other]
            label_ok = len(other)==1 and _literal(label)==_literal(paired[0][0])
            code_ok = len(other)==1 and code is not None and code==paired[0][1]
            label_words = [word for r in [row,*other] for word in r["words"][:-1 if code else None]
                           if re.search(r"[A-Za-z0-9]",word["text"])]
            code_words = [r["words"][-1] for r in [row,*other]] if code else []
            label_confidence = min((word["confidence"] for word in label_words),default=0.0)
            code_confidence = min((word["confidence"] for word in code_words),default=0.0)
            label_supported = bool(label_ok and label_confidence>=MIN_CONFIDENCE and _ink_support(ink,label_words))
            code_supported = bool(code_ok and code_confidence>=MIN_CONFIDENCE and _ink_support(ink,code_words))
            identifier = "a2row:"+_digest([image_hash,row["pixel_bbox"],label,code])[:24]
            child = {"id":identifier,"kind":"process","label":label,"code":code or "",
                     "region":_page_region(row["pixel_bbox"],geometry),"designation_parse":method,
                     "observed_pixel_bbox":row["pixel_bbox"]}
            nodes.append(child);processes.append(child)
            decisions[identifier] = {"label_supported":label_supported,
                "designation_supported":code_supported,"primary_confidence":row["confidence"],
                "label_confidence":label_confidence,"designation_confidence":code_confidence,
                "corroborating_row_count":len(other),"criterion":"two_local_ocr_readings_agree_above_80_confidence_and_visible_ink"}
            edge = {"from":group["id"],"to":identifier,"type":"ENCLOSES_ROW", "region":child["region"]}
            edges.append(edge)
            key = _json([edge["from"],edge["to"],edge["type"]])
            unique = sum(_inside(value["box"],row["pixel_bbox"],2) for value in groups)==1
            enclosures[key] = {"from_id":group["id"],"to_id":identifier,"verified":bool(unique),
                "criterion":"native_closed_rectangle_and_unique_observed_row_enclosure"}
        # This is a displayed indentation relation only; it never grants IS_A.
        stack = []
        for child in processes:
            left = child["observed_pixel_bbox"][0]
            threshold = max(6, child["observed_pixel_bbox"][3]*.6)
            while stack and left <= stack[-1][1]+threshold:
                stack.pop()
            if stack:
                parent = stack[-1][0]
                edges.append({"from":parent["id"],"to":child["id"],"type":"INDENTED_UNDER",
                    "region":_page_region(_union([parent["observed_pixel_bbox"],child["observed_pixel_bbox"]]),geometry)})
            stack.append((child,left))
        missing_bands = _uncovered_text_bands(ink,group["box"],group["rows"])
        word_ids = {word["tsv_row_index"] for row in group["rows"] for word in row["words"]}
        assigned = {word["tsv_row_index"] for word in primary if _inside(group["box"],word["pixel_bbox"],2)}
        literal_complete = decisions[node["id"]]["label_supported"] and all(
            decisions[child["id"]]["label_supported"] and decisions[child["id"]]["designation_supported"] for child in processes)
        observed_complete = not missing_bands and assigned==word_ids
        if group is not root:
            coverage[node["id"]] = {"scope":"selected_A2_box", "box_role":"row_group" if body else "container",
                "observed_rows_complete":bool(observed_complete), "accepted_literals_complete":bool(literal_complete),
                "complete":bool(observed_complete and literal_complete),"process_ids":[child["id"] for child in processes],
                "observed_body_row_count":len(body),"uncovered_ink_bands":missing_bands,
                "qualification":"Scoped observed rows/ink; no reference counts or semantic taxonomy used."}
    # Reuse A1's existing source-local glyph checks for uncertain printed codes.
    # Targets never supply their own templates, even via the other OCR reading.
    from src.evidence_a1_verification import _glyphs, _glyph_corrob
    bank,code_words = {},{}
    for node in nodes:
        if node["kind"]!="process" or not node["code"]:
            continue
        words = sorted([word for word in primary if _inside(node["observed_pixel_bbox"],word["pixel_bbox"],2)],
                       key=lambda word:word["pixel_bbox"][0])
        if not words or words[-1]["text"]!=node["code"]:
            continue
        word = dict(words[-1],id=node["id"])
        code_words[node["id"]] = word
        glyphs = _glyphs(ink>0,word)
        if (word["confidence"]>=90 and decisions[node["id"]]["label_supported"]
                and decisions[node["id"]]["designation_supported"] and len(glyphs)==len(node["code"])):
            for index,(letter,(mask,box)) in enumerate(zip(node["code"],glyphs)):
                bank.setdefault(letter,[]).append((mask,node["id"],index,box))
    for node in nodes:
        decision = decisions[node["id"]]
        if node["id"] not in code_words or decision["designation_supported"] or not decision["label_supported"]:
            continue
        passed,corroboration = _glyph_corrob(ink>0,code_words[node["id"]],node["code"],bank)
        decision["designation_glyph_corroboration"] = corroboration
        if passed:
            decision["designation_supported"] = True
            decision["support_node_ids"] = sorted({item["template_word_id"] for item in corroboration["glyphs"]})
            decision["designation_criterion"] = "existing_source_local_glyph_iou_80_margin_05_target_excluded"
    for identifier,value in coverage.items():
        literals = decisions[identifier]["label_supported"] and all(
            decisions[child]["label_supported"] and decisions[child]["designation_supported"] for child in value["process_ids"])
        value.update(accepted_literals_complete=bool(literals),
                     complete=bool(value["observed_rows_complete"] and literals))
    connector_records = _physical_connectors(geometry,box_nodes,ink)
    neighbors = {identifier:set() for identifier in box_nodes}
    for record in connector_records:
        if record["verified"]:
            first,last = record["end_ids"]
            neighbors[first].add(last);neighbors[last].add(first)
    parents,queue = {root["id"]:None},deque([root["id"]])
    while queue:
        parent = queue.popleft()
        for child in sorted(neighbors[parent]):
            if child == parents[parent]:
                continue
            if child in parents:
                raise ValueError("A2_PHYSICAL_GRAPH_NOT_TREE")
            parents[child] = parent;queue.append(child)
    oriented = []
    for record in connector_records:
        first,last = record["end_ids"]
        if parents.get(last)==first:
            start,end = first,last
        elif parents.get(first)==last:
            start,end = last,first
        else:
            continue
        item = {**record,"from_id":start,"to_id":end,"path_order":"away_from_caption_matched_root_for_navigation_only"}
        oriented.append(item)
        edges.append({"from":start,"to":end,"type":"CHART_CONNECTOR","region":item["region"],
            "polyline_pixel_endpoints":item["pixel_endpoints"],"direction":"undirected"})
    rectangle_complete = set(parents)==set(box_nodes)
    closure = _chart_closure(ink,groups,primary,oriented)
    for value in coverage.values():
        value["pixel_chart_closure_complete"] = closure["complete"]
        value["complete"] = bool(value["complete"] and closure["complete"])
    chart_complete = (rectangle_complete and closure["complete"] and all(item["complete"] for item in coverage.values())
                      and decisions[root["id"]]["label_supported"])
    receipt = {"schema_version":"chart-source-record-verification-1.0","image_sha256":image_hash,
        "nodes":decisions,"enclosures":enclosures,"coverage":coverage,
        "criteria":{"minimum_ocr_confidence":MIN_CONFIDENCE,"minimum_connector_ink_coverage":.97,
            "literal_checks":"whole-region sparse OCR and per-box block OCR agree; uncertain codes need existing same-image glyph corroboration with target excluded",
            "admission_limit":"Literal recognition/physical layout only; automatic heuristics, not human review or semantic proof."},
        "chart_coverage":{"scope":"selected_A2_native_rectangles_and_observed_OCR_rows", "complete":bool(chart_complete),
            "connected_box_inventory_complete":rectangle_complete,"native_rectangle_count":len(box_nodes),
            "observed_process_row_count":sum(node["kind"]=="process" for node in nodes),
            "pixel_chart_closure":closure,
            "qualification":"Figure A2 crop only; A3 and unseen corpus completeness are not covered."}}
    source_id = source["source_identity_id"]
    parent_binding = {key:source[key] for key in ("edition_id","source_identity_id","locator")}
    parent_binding["asset_sha256"] = source["manifest_asset_sha256"]
    graph = {"schema_version":"a1-geometry-1.0","region_space":"normalized_pdf_page_ymin_xmin_ymax_xmax",
        "root_id":root["id"],"nodes":nodes,"edges":edges,
        "edge_qualifications":{
            "ENCLOSES_ROW":{"verification":"candidate","qualification":"Observed native box enclosure, individually checked before knowledge admission; no subtype."},
            "CHART_CONNECTOR":{"verification":"candidate","qualification":"Native-line/pixel physical connection; navigation orientation only, not arrow or semantic direction."},
            "INDENTED_UNDER":{"verification":"candidate","qualification":"Displayed relative indentation only; no accepted semantic subtype."}},
        "extraction_provenance":{"method":"ocr","engine":"tesseract+native-vector","version":seed["engine_version"],
            "input_asset_sha256":image_hash,"uncertainty":"unreviewed_model_observation","parent_source":parent_binding},
        "raster_verification":{"schema_version":"chart-source-integration-1.0","artifacts":artifacts,
            "receipt":receipt,"connector_receipt":{"records":oriented,"direction":"undirected"}},
        "adapter_version":VERSION}
    from src.evidence_a1 import bind_chart_graph_evidence
    return bind_chart_graph_evidence(graph,source["edition_id"],source_id,source["locator"],image_hash)


def ingest(root, directory, *, primary_ocr_cache=None):
    """One local extraction; retained readings are replayed for subsequent queries."""
    import cv2
    import numpy as np
    root = Path(root).resolve(strict=True)
    directory = _private(root,directory)
    directory.mkdir(parents=True,exist_ok=False)
    started = time.perf_counter()
    source,geometry,image_bytes = _source(root)
    image_path = directory/"figure_a2_crop.png"
    with image_path.open("xb") as stream:
        stream.write(image_bytes)
    calls = 0
    if primary_ocr_cache is None:
        primary_tsv = _run_tesseract(image_path,"eng",11,120);calls+=1
        primary_provenance = {"cache_reused":False,"psm":11}
    else:
        cache = _private(root,primary_ocr_cache)
        # Cache reuse requires the original image bytes alongside the inspection.
        original_image = cache.parent/"a2_crop_300.png"
        if not original_image.is_file() or original_image.read_bytes()!=image_bytes:
            raise ValueError("A2_OCR_CACHE_IMAGE_MISMATCH")
        primary_tsv = cache.read_text(encoding="utf-8")
        primary_provenance = {"cache_reused":True,"psm":11,"cache_sha256":_sha(cache.read_bytes()),
            "cache_relpath":cache.relative_to(root).as_posix(),"original_inspection_ocr_calls":1}
    image = cv2.imdecode(np.frombuffer(image_bytes,dtype=np.uint8),cv2.IMREAD_COLOR)
    secondary = []
    for index,rectangle in enumerate(geometry["rectangles"]):
        box = _pixel_box(rectangle["pdf_bbox"],geometry)
        x,y,w,h = box
        patch_box = [x+4,y+4,w-8,h-8]
        px,py,pw,ph = patch_box
        path = directory/("box_"+str(index)+".png")
        if not cv2.imwrite(str(path),image[py:py+ph,px:px+pw]):
            raise ValueError("A2_OCR_PATCH_WRITE_FAILED")
        tsv = _run_tesseract(path,"eng",6,120);calls+=1
        secondary.append({"box_index":index,"pixel_bbox":box,"patch_bbox":patch_box,"psm":6,"tsv":tsv})
    seed = {"schema_version":"a2-retained-extraction-1.0","adapter_version":VERSION,"source":source,
        "geometry":geometry,"engine_version":_engine_version(),"renderer_version":version("PyMuPDF"),
        "primary_ocr":{"tsv":primary_tsv,**primary_provenance},"secondary_ocr":secondary,
        "ocr_invocations":calls,"historical_inspection_ocr_invocations":int(primary_provenance["cache_reused"]),
        "model_calls":0,"external_calls":0,"elapsed_extraction_seconds":time.perf_counter()-started}
    seed_path = directory/"ingest_result.json"
    write_private_output(root,seed_path,seed)
    artifacts = {"ingest_result":{"path":seed_path.relative_to(root).as_posix(),"sha256":_sha(seed_path.read_bytes())},
                 "image":{"path":image_path.relative_to(root).as_posix(),"sha256":_sha(image_bytes)}}
    graph = _assemble(seed,image_bytes,artifacts)
    write_private_output(root,directory/"graph.json",graph)
    return {"schema_version":"a2-ingest-receipt-1.0","source_element":ELEMENT,
        "graph_path":(directory/"graph.json").relative_to(root).as_posix(),"source":source,
        "graph_sha256":_digest(graph),"ocr_invocations":calls,"model_calls":0,"external_calls":0,
        "node_count":len(graph["nodes"]),"edge_count":len(graph["edges"]),
        "verification":graph["raster_verification"]["receipt"]["chart_coverage"]}


def _retained_inputs(root, graph):
    """Authenticate source, exact crop and retained extraction before replay."""
    root = Path(root).resolve(strict=True)
    metadata = graph.get("raster_verification",{})
    if metadata.get("schema_version") != "chart-source-integration-1.0":
        raise ValueError("A2_VERIFICATION_SCHEMA_INVALID")
    artifacts = metadata.get("artifacts",{})
    if set(artifacts) != {"ingest_result","image"}:
        raise ValueError("A2_ARTIFACTS_INVALID")
    payloads = {}
    for name,item in artifacts.items():
        if not isinstance(item,dict) or set(item)!={"path","sha256"}:
            raise ValueError("A2_ARTIFACT_INVALID")
        path = _private(root,item["path"])
        payloads[name] = path.read_bytes()
        if _sha(payloads[name])!=item["sha256"]:
            raise ValueError("A2_RETAINED_ARTIFACT_CHANGED")
    seed = json.loads(payloads["ingest_result"])
    source,geometry,image = _source(root)
    if (seed.get("schema_version")!="a2-retained-extraction-1.0" or seed["source"]!=source
            or seed["geometry"]!=geometry or payloads["image"]!=image):
        raise ValueError("A2_CANONICAL_SOURCE_MISMATCH")
    return seed,image,artifacts


def validate_a2_integration(root, graph):
    """Authenticate source/retained bytes and recompute every admission decision."""
    seed,image,artifacts = _retained_inputs(root,graph)
    expected = _assemble(seed,image,artifacts)
    if expected != graph:
        raise ValueError("A2_SOURCE_PROJECTION_MISMATCH")
    return deepcopy(expected["raster_verification"]["receipt"])


def reproject(root, graph_path, output):
    """Preserve an old extraction while writing a new deterministic projection."""
    original = json.loads(_private(root,graph_path,suffix=".json").read_text(encoding="utf-8"))
    seed,image,artifacts = _retained_inputs(root,original)
    graph = _assemble(seed,image,artifacts)
    write_private_output(root,output,graph)
    return {"schema_version":"a2-projection-receipt-1.0","source_element":ELEMENT,
        "projection_version":VERSION,"projection_path":str(output),"graph_sha256":_digest(graph),
        "retained_extraction_version":seed["adapter_version"],"ocr_invocations":0,"model_calls":0,"external_calls":0,
        "verification":graph["raster_verification"]["receipt"]["chart_coverage"]}


def run_questions(root, graph_path, payload, *, query_layer="auto", question_planner=None):
    """Execute the existing typed backend; grading data is never accepted here."""
    if (not isinstance(payload,dict) or set(payload)!={"schema_version","source_element","questions"}
            or payload["schema_version"]!="a2-development-cq-1.0" or payload["source_element"]!=ELEMENT
            or not isinstance(payload["questions"],list)):
        raise ValueError("A2_QUESTION_INPUT_INVALID")
    seen = set()
    for item in payload["questions"]:
        if (not isinstance(item,dict) or set(item)!={"id","query"} or not isinstance(item["id"],str)
                or not item["id"] or item["id"] in seen or not isinstance(item["query"],str)
                or not item["query"].strip() or len(item["query"])>10000):
            raise ValueError("A2_QUESTION_ITEM_INVALID")
        seen.add(item["id"])
    from src.evidence_a1_graph_qa import answer_graph,HARNESS_VERSION
    from src.evidence_a1_knowledge import prepare_chart_knowledge
    root = Path(root).resolve(strict=True)
    graph_path = _private(root,graph_path,suffix=".json")
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    validate_a2_integration(root,graph)
    runtime = graph_path.with_suffix(".registry.db").relative_to(root).as_posix()
    store = prepare_chart_knowledge(root,graph,runtime_relpath=runtime)
    answers = []
    for item in payload["questions"]:
        started = time.perf_counter()
        answer = answer_graph(graph,item["query"],knowledge_store=store,query_layer=query_layer,
                              question_planner=question_planner)
        answers.append({"id":item["id"],"owner_query":item["query"],"result":answer,
                        "latency_seconds":time.perf_counter()-started})
        if callable(getattr(question_planner,"record_result",None)):
            question_planner.record_result(answers[-1])
    return {"schema_version":"a2-graph-qa-results-1.0","source_element":ELEMENT,
        "harness_version":HARNESS_VERSION,"adapter_version":VERSION,"generation_model":"NONE",
        "model":getattr(question_planner,"metadata",{}).get("model","NONE"),
        "evaluation_kind":"LLM_planned_deterministic_retrieval" if question_planner is not None else "deterministic_graph_retrieval",
        "model_calls":len(getattr(question_planner,"calls",[])),
        "planner":getattr(question_planner,"metadata","deterministic"),
        "external_calls":sum(call.get("external_call_count",0) for call in getattr(question_planner,"calls",[])),
        "query_layer":query_layer,"graph_sha256":_digest(graph),
        "knowledge":store.describe(),"answers":answers}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root",type=Path,default=Path(__file__).resolve().parents[1])
    sub = parser.add_subparsers(dest="command",required=True)
    extraction = sub.add_parser("ingest")
    extraction.add_argument("--directory",required=True,type=Path)
    extraction.add_argument("--primary-ocr-cache",type=Path)
    extraction.add_argument("--output",required=True,type=Path)
    projection = sub.add_parser("reproject")
    projection.add_argument("--graph",required=True,type=Path)
    projection.add_argument("--graph-output",required=True,type=Path)
    projection.add_argument("--output",required=True,type=Path)
    qa = sub.add_parser("query")
    qa.add_argument("--graph",required=True,type=Path)
    qa.add_argument("--input",required=True,type=Path)
    qa.add_argument("--output",required=True,type=Path)
    qa.add_argument("--layer",choices=["auto","evidence","knowledge"],default="auto")
    qa.add_argument("--planner-directory","--local-planner-directory",dest="local_planner_directory",type=Path,
                    help="Opt-in planner; retain exact requests in a new private directory")
    qa.add_argument("--planner-provider",choices=["ollama","deepseek"],default="ollama")
    args = parser.parse_args(argv)
    if args.command=="ingest":
        result = ingest(args.root,args.directory,primary_ocr_cache=args.primary_ocr_cache)
    elif args.command=="reproject":
        result = reproject(args.root,args.graph,args.graph_output)
    else:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        planner = None
        if args.local_planner_directory:
            from src.evidence_chart_local_planner import create_question_planner
            planner = create_question_planner(args.root,args.local_planner_directory,args.planner_provider)
        result = run_questions(args.root,args.graph,payload,query_layer=args.layer,question_planner=planner)
    write_private_output(args.root,args.output,result)
    print(_json({"status":"complete","output":str(args.output),
                 "model_calls":result.get("model_calls",0),"generation_model":"NONE",
                 "planning_model":result.get("model","NONE"),"external_calls":result.get("external_calls",0)}))


if __name__=="__main__":
    main()
