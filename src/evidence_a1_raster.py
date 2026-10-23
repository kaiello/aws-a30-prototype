"""Image-only OCR and geometry candidates for a rectangular process chart.

The default route reads pixels alone. The optional dictionary-assisted route
also consumes a declared literal label/code vocabulary, never source geometry,
relationships or answers. Raw OCR stays intact. Its output remains an unbound
candidate graph, never accepted knowledge or proof of complete chart coverage.
"""
from __future__ import annotations

import csv
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import statistics
import subprocess


RASTER_VERSION = "a1-raster-geometry-1.1.0"
_EDGE_QUALIFICATIONS = {
    "ENCLOSES_ROW": {"verification":"candidate", "qualification":"OCR row assigned to a detected rectangle; unreviewed raster enclosure candidate."},
    "CHART_CONNECTOR": {"verification":"candidate", "qualification":"Detected line component touches two rectangle boundaries; unreviewed connector candidate."},
    "INDENTED_UNDER": {"verification":"candidate", "qualification":"Nearest preceding row at a lower image indentation; not an accepted semantic subtype."},
}


def _run_tesseract(image_path, language, psm, timeout_s):
    executable = shutil.which("tesseract")
    if executable is None:
        raise RuntimeError("TESSERACT_NOT_INSTALLED")
    result = subprocess.run([executable,str(image_path),"stdout","-l",language,"--psm",str(psm),"tsv"],
                            capture_output=True,text=True,encoding="utf-8",errors="replace",
                            timeout=timeout_s,check=True)
    return result.stdout


def _engine_version():
    executable = shutil.which("tesseract")
    if executable is None:
        return None
    result = subprocess.run([executable,"--version"],capture_output=True,text=True,
                            encoding="utf-8",errors="replace",timeout=10,check=True)
    return result.stdout.splitlines()[0] if result.stdout else None


def _region(box, width, height):
    x,y,w,h = box
    return [round(y/height,8),round(x/width,8),round((y+h)/height,8),round((x+w)/width,8)]


def _union(boxes):
    x = min(box[0] for box in boxes)
    y = min(box[1] for box in boxes)
    right = max(box[0]+box[2] for box in boxes)
    bottom = max(box[1]+box[3] for box in boxes)
    return [x,y,right-x,bottom-y]


def _identifier(edition_id, image_hash, kind, value):
    digest = hashlib.sha256(f"{edition_id}\0{image_hash}\0{kind}\0{value}".encode()).hexdigest()[:20]
    return f"raster:{kind}:{digest}"


def _words_from_tsv(tsv, width, height):
    words, rejected = [], []
    for index,row in enumerate(csv.DictReader(io.StringIO(tsv),delimiter="\t")):
        if row.get("level") != "5" or not row.get("text","").strip():
            continue
        try:
            box = [int(row[key]) for key in ("left","top","width","height")]
            confidence = float(row["conf"])
        except (ValueError,KeyError,TypeError):
            rejected.append({"row_index":index,"reason":"invalid_tsv_word_geometry"})
            continue
        x,y,w,h = box
        if w<=0 or h<=0 or x<0 or y<0 or x+w>width or y+h>height:
            rejected.append({"row_index":index,"reason":"word_outside_image"})
            continue
        words.append({"text":row["text"].strip(),"pixel_bbox":box,"confidence":confidence,"tsv_row_index":index})
    return words,rejected


def _rectangles(image, *, repair_border_gaps=False):
    import cv2
    height,width = image.shape[:2]
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    ink = cv2.threshold(gray,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)[1]
    horizontal = cv2.morphologyEx(ink,cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT,(max(15,width//45),1)))
    vertical = cv2.morphologyEx(ink,cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT,(1,max(15,height//45))))
    lines = cv2.bitwise_or(horizontal,vertical)
    contour_lines = lines
    if repair_border_gaps:
        # Rasterization can leave a short gap where thin horizontal and vertical
        # borders meet. Repair only a few pixels, not missing diagram segments.
        radius = max(2, round(min(width, height) * .0008))
        # Use a narrow contour tolerance rather than altering the line evidence
        # supplied to connector analysis below.
        contour_lines = cv2.dilate(lines,
            cv2.getStructuringElement(cv2.MORPH_RECT, (2*radius+1, 2*radius+1)))
    contours,_ = cv2.findContours(contour_lines,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
    candidates = []
    for contour in contours:
        perimeter = cv2.arcLength(contour,True)
        polygon = cv2.approxPolyDP(contour,0.018*perimeter,True)
        x,y,w,h = cv2.boundingRect(contour)
        if (len(polygon)!=4 or not cv2.isContourConvex(polygon) or w<max(30,width*.10)
                or h<max(20,height*.025) or w*h<width*height*.002 or w*h>width*height*.85):
            continue
        if cv2.contourArea(contour)/(w*h)<.80:
            continue
        candidates.append([x,y,w,h])
    # The inner and outer contours of a printed border are the same rectangle.
    distinct = []
    for box in sorted(candidates,key=lambda item:item[2]*item[3],reverse=True):
        if any(_intersection_area(box,other)/max(box[2]*box[3],other[2]*other[3])>.85 for other in distinct):
            continue
        distinct.append(box)
    # Header separators can create smaller contours inside a single group box.
    boxes = [box for box in distinct if not any(_contains(other,box,margin=2) for other in distinct if other!=box)]
    return sorted(boxes,key=lambda box:(box[1],box[0])),lines


def _intersection_area(left, right):
    return max(0,min(left[0]+left[2],right[0]+right[2])-max(left[0],right[0])) * max(
        0,min(left[1]+left[3],right[1]+right[3])-max(left[1],right[1]))


def _contains(outer, inner, margin=0):
    return (outer[0]-margin<=inner[0] and outer[1]-margin<=inner[1]
            and inner[0]+inner[2]<=outer[0]+outer[2]+margin
            and inner[1]+inner[3]<=outer[1]+outer[3]+margin)


def _rows(words):
    grouped = []
    for word in sorted(words,key=lambda item:(item["pixel_bbox"][1],item["pixel_bbox"][0])):
        box = word["pixel_bbox"]
        center = box[1]+box[3]/2
        matches = [row for row in grouped if abs(row["center"]-center)<=max(box[3],row["height"])*.55]
        if matches:
            row = min(matches,key=lambda item:abs(item["center"]-center))
            row["words"].append(word)
            row["center"] = statistics.mean(item["pixel_bbox"][1]+item["pixel_bbox"][3]/2 for item in row["words"])
            row["height"] = statistics.median(item["pixel_bbox"][3] for item in row["words"])
        else:
            grouped.append({"words":[word],"center":center,"height":box[3]})
    result = []
    for row in sorted(grouped,key=lambda item:item["center"]):
        ordered = sorted(row["words"],key=lambda item:item["pixel_bbox"][0])
        result.append({"words":ordered,"text":" ".join(item["text"] for item in ordered),
                       "pixel_bbox":_union([item["pixel_bbox"] for item in ordered]),
                       "confidence":min(item["confidence"] for item in ordered)})
    return result


def _designation(row, box):
    identity = row.get("normalized_identity")
    if identity and identity["kind"] == "process" and identity.get("code"):
        return identity["label"], identity["code"], "dictionary_assisted_observed_pair"
    matched = re.fullmatch(r"(.*?)\s*\(\s*([A-Z][A-Z0-9]*(?:\s*-\s*[A-Z0-9]+)*)\s*\)\s*",row["text"])
    if matched and matched[1].strip():
        return matched[1].strip(),re.sub(r"\s+","",matched[2]),"terminal_parentheses"
    tokens = row["words"]
    if len(tokens)>1 and re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*",tokens[-1]["text"]):
        previous,last = tokens[-2]["pixel_bbox"],tokens[-1]["pixel_bbox"]
        gap = last[0]-(previous[0]+previous[2])
        if gap>=max(statistics.median(item["pixel_bbox"][3] for item in tokens)*1.25,box[2]*.035):
            return " ".join(item["text"] for item in tokens[:-1]),tokens[-1]["text"],"separated_right_column"
    return row["text"],None,"unresolved_designation"


def _dictionary_entries(dictionary, edition_id):
    """Validate a vocabulary-only handoff, with no geometry or relationship data."""
    if dictionary is None:
        return None
    if not isinstance(dictionary, dict) or set(dictionary) != {
            "schema_version", "source", "entries", "content_sha256"}:
        raise ValueError("RASTER_DICTIONARY_CONTRACT_INVALID")
    source = dictionary["source"]
    if (dictionary["schema_version"] != "a1-normalization-dictionary-1.0"
            or not isinstance(source, dict) or set(source) != {
                "edition_id", "source_identity_id", "asset_sha256", "lexicon_version"}
            or source["edition_id"] != edition_id
            or not all(isinstance(value, str) and value for value in source.values())):
        raise ValueError("RASTER_DICTIONARY_SOURCE_INVALID")
    payload = {key: value for key, value in dictionary.items() if key != "content_sha256"}
    actual = hashlib.sha256(json.dumps(payload, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    if dictionary["content_sha256"] != actual:
        raise ValueError("RASTER_DICTIONARY_HASH_INVALID")
    if not isinstance(dictionary["entries"], list):
        raise ValueError("RASTER_DICTIONARY_ENTRIES_INVALID")
    for entry in dictionary["entries"]:
        if (not isinstance(entry, dict) or not {"kind", "label"} <= set(entry)
                or not set(entry) <= {"kind", "label", "code"}
                or entry["kind"] not in {"root", "category", "process"}
                or not isinstance(entry["label"], str) or not entry["label"].strip()
                or not re.search(r"[a-z0-9]", entry["label"], re.I)
                or ("code" in entry and (not isinstance(entry["code"], str) or not entry["code"]))):
            raise ValueError("RASTER_DICTIONARY_ENTRIES_INVALID")
    return dictionary["entries"]


def _literal_words(text):
    return tuple(re.findall(r"[a-z0-9]+", text.casefold()))


def _one_code_edit(left, right):
    """A small code correction is allowed only beside an exact observed name."""
    if len(left) < 3 or len(right) < 3:
        return False
    if len(left) == len(right):
        return sum(a != b for a, b in zip(left, right)) == 1
    if abs(len(left) - len(right)) != 1:
        return False
    shorter, longer = sorted((left, right), key=len)
    return any(longer[:index] + longer[index+1:] == shorter for index in range(len(longer)))


def _normalize_observed_row(row, entries):
    """Match an observed name/code pair; absent or ambiguous text is not filled in."""
    text = row["text"].strip()
    candidates = []
    known_codes = {entry["code"].upper() for entry in entries if entry.get("code")}
    for entry in entries:
        label_words = _literal_words(entry["label"])
        # A code is a separate observed suffix, whether parenthesized or simply
        # in the right column. Hyphens/punctuation inside the name are matching
        # normalization, not additional aliases.
        pattern = r"^\s*" + r"[\W_]+".join(map(re.escape, label_words))
        matched = re.match(pattern + r"(?=$|[\W_])", text, re.I)
        if not matched:
            continue
        tail = text[matched.end():].strip().strip("()").strip()
        expected = entry.get("code")
        if expected:
            observed = re.sub(r"\s+", "", tail).upper()
            if not observed:
                continue  # A known label alone does not manufacture its code.
            exact = observed == expected.upper()
            corrected = (observed not in known_codes
                         and _one_code_edit(observed, expected.upper()))
            if not (exact or corrected):
                continue
            candidates.append((entry, "exact_observed_name_code" if exact
                               else "exact_name_single_code_edit", tail))
        elif not tail:
            candidates.append((entry, "exact_observed_label", None))
    if not candidates:
        return None
    unique = {(item[0]["kind"], item[0]["label"], item[0].get("code")) for item in candidates}
    if len(unique) != 1:
        row["normalization"] = {"status": "ambiguous", "raw_text": text,
            "candidates": [{key: entry[key] for key in ("kind", "label", "code") if key in entry}
                           for entry, _, _ in candidates]}
        return None
    entry, method, observed_code = candidates[0]
    row["normalized_identity"] = dict(entry)
    row["normalization"] = {"status": "matched_candidate", "method": method,
        "raw_text": text, "observed_code": observed_code,
        "normalized_label": entry["label"], "normalized_code": entry.get("code")}
    return row["normalized_identity"]


def _assisted_group_identity(group, entries):
    combined = {"text": " ".join(row["text"] for row in group["rows"])}
    identity = _normalize_observed_row(combined,
        [entry for entry in entries if entry["kind"] == "root"])
    if identity:
        group["normalized_identity"] = identity
        group["normalization"] = combined["normalization"]
    return identity


def _connector_contacts(lines, boxes):
    import cv2
    import numpy as np
    height,width = lines.shape[:2]
    remaining = lines.copy()
    pad = max(3,round(min(width,height)*.006))
    for x,y,w,h in boxes:
        cv2.rectangle(remaining,(x,y),(x+w-1,y+h-1),0,max(3,pad))
    count,labels,stats,_ = cv2.connectedComponentsWithStats(remaining,8)
    components = []
    for label in range(1,count):
        x,y,w,h,area = [int(item) for item in stats[label]]
        if area<max(10,min(width,height)*.02):
            continue
        component = labels==label
        contacts = []
        for index,(bx,by,bw,bh) in enumerate(boxes):
            left,top,right,bottom = max(0,bx-pad*2),max(0,by-pad*2),min(width,bx+bw+pad*2),min(height,by+bh+pad*2)
            if np.any(component[top:bottom,left:right]):
                contacts.append(index)
        if len(contacts)>1:
            components.append({"pixel_bbox":[x,y,w,h],"box_indices":contacts})
    return components


def _project_graph_candidates(groups, edition_id, image_hash, width, height, root=None):
    """Project the same parsed OCR rows with or without a resolved root box."""
    nodes,edges,unresolved = [],[],[]

    def node(kind, label, box, observation_ids, **fields):
        identifier = _identifier(edition_id,image_hash,kind,f"{box}|{label}")
        record = {"id":identifier,"kind":kind,"label":label,"region":_region(box,width,height),
                  "observation_ids":list(observation_ids),"verification":"candidate",**fields}
        nodes.append(record)
        return record

    def edge(source, target, kind, box, observation_ids):
        edges.append({"from":source["id"],"to":target["id"],"type":kind,"region":_region(box,width,height),
                      "observation_ids":list(dict.fromkeys(observation_ids)),"verification":"candidate"})

    root_node = None
    if root is not None:
        root_label = root.get("normalized_identity", {}).get("label") or " ".join(row["text"] for row in root["rows"])
        root_node = node("root",root_label,root["box"],
            [root["rectangle_id"],*[row["observation_id"] for row in root["rows"]]])
        if root.get("normalization"):
            root_node["normalization"] = deepcopy(root["normalization"])
    category_nodes = {}
    for group in groups:
        if group is root:
            continue
        if len(group["rows"])<2:
            unresolved.append({"kind":"category_rows_not_established","rectangle_id":group["rectangle_id"]})
            continue
        heading,*body = group["rows"]
        identity = heading.get("normalized_identity", {})
        category_label = heading["text"]
        if identity.get("kind") == "category":
            category_label = identity["label"] + (f" ({identity['code']})" if identity.get("code") else "")
        category = node("category",category_label,group["box"],[group["rectangle_id"],heading["observation_id"]])
        if heading.get("normalization"):
            category["normalization"] = deepcopy(heading["normalization"])
        category_nodes[group["index"]] = category
        parsed = []
        for row_index,row in enumerate(body):
            label,code,method = _designation(row,group["box"])
            if not code:
                unresolved.append({"kind":"row_designation_unresolved","observation_id":row["observation_id"],
                                   "category_id":category["id"]})
                continue
            process = node("process",label,row["pixel_bbox"],[row["observation_id"]],code=code,
                           designation_method=method,ocr_confidence=row["confidence"],row_order=row_index)
            if row.get("normalization"):
                process["normalization"] = deepcopy(row["normalization"])
            edge(category,process,"ENCLOSES_ROW",_union([group["box"],row["pixel_bbox"]]),
                 [group["rectangle_id"],row["observation_id"]])
            parsed.append((row,process))
        if not parsed:
            unresolved.append({"kind":"category_has_no_resolved_process_rows","category_id":category["id"]})
            continue
        indent_threshold = statistics.median(row["pixel_bbox"][3] for row,_ in parsed)*.65
        history = []
        for row,process in parsed:
            x = row["pixel_bbox"][0]
            parents = [(other,parent) for other,parent in history if other["pixel_bbox"][0]+indent_threshold<x]
            if parents:
                prior,parent = parents[-1]
                edge(parent,process,"INDENTED_UNDER",_union([prior["pixel_bbox"],row["pixel_bbox"]]),
                     [prior["observation_id"],row["observation_id"]])
            history.append((row,process))
    graph = {"schema_version":"a1-geometry-1.0","root_id":root_node["id"] if root_node else None,"nodes":nodes,"edges":edges,
        "edge_qualifications":{kind:dict(value) for kind,value in _EDGE_QUALIFICATIONS.items()},
        "region_space":"normalized_pdf_page_ymin_xmin_ymax_xmax","native_text":"",
        "ocr_text":"\n".join(row["text"] for group in groups for row in group["rows"]),
        "limits":["Raw image-only OCR/CV candidates; source authentication and review are separate.",
                  "Rectangular-box/first-heading style assumption; coverage is not established.",
                  "No accepted semantic subtype or native-PDF observation is produced."]}
    if root_node is None:
        graph["limits"].append("Partial projection lacks a root; it is not an executable canonical graph.")
    return graph,category_nodes,root_node,unresolved


def rebuild_partial_from_observations(extracted, *, dictionary=None):
    """Return a missing-root projection using cached observations only.

    No image, native text, OCR process or CV operation is read or executed here.
    The original extraction is not mutated. Root/connector interpretation remains
    unresolved for a separate, explicitly authorized visual interpretation step.
    """
    result = deepcopy(extracted)
    if result.get("graph") is not None:
        return result
    source = result["input"]
    edition_id,image_hash,width,height = (source[key] for key in ("edition_id","image_sha256","width","height"))
    dictionary_entries = _dictionary_entries(dictionary, edition_id)
    observations = result.get("observations",[])
    by_id = {item["id"]:item for item in observations}
    if len(by_id)!=len(observations) or any(item.get("edition_id")!=edition_id or item.get("image_sha256")!=image_hash for item in observations):
        raise ValueError("RASTER_CACHED_OBSERVATION_SCOPE_INVALID")
    rectangles = [item for item in observations if item["kind"]=="visual_rectangle"]
    row_observations = [item for item in observations if item["kind"]=="ocr_row"]
    groups = []
    unresolved = result.setdefault("diagnostics",{}).setdefault("unresolved_visual_structures",[])
    for index,rectangle in enumerate(rectangles):
        rows = []
        for observed in row_observations:
            containers = [item for item in rectangles if _contains(item["pixel_bbox"],observed["pixel_bbox"],margin=2)]
            if len(containers)!=1 or containers[0]["id"]!=rectangle["id"]:
                continue
            word_ids = observed.get("word_observation_ids",[])
            if not word_ids or any(identifier not in by_id or by_id[identifier]["kind"]!="ocr_word" for identifier in word_ids):
                unresolved.append({"kind":"cached_row_word_proof_incomplete","observation_id":observed["id"]})
                continue
            words = [{"text":by_id[identifier]["text"],"pixel_bbox":by_id[identifier]["pixel_bbox"],
                      "confidence":by_id[identifier]["confidence"],"observation_id":identifier} for identifier in word_ids]
            row = {"text":observed["text"],"pixel_bbox":observed["pixel_bbox"],"confidence":observed["confidence"],
                   "words":words,"observation_id":observed["id"]}
            if dictionary_entries is not None:
                _normalize_observed_row(row, dictionary_entries)
            rows.append(row)
        group = {"index":index,"box":rectangle["pixel_bbox"],"rows":rows,
                 "rectangle_id":rectangle["id"]}
        if dictionary_entries is not None:
            _assisted_group_identity(group, dictionary_entries)
        groups.append(group)
    # Same frozen root classification. Possible compact roots must not silently
    # become category boxes merely because the root decision was ambiguous.
    roots = ([group for group in groups if group.get("normalized_identity", {}).get("kind") == "root"]
        if dictionary_entries is not None else
        [group for group in groups if group["rows"] and len(group["rows"])<=2
         and group["box"][3]<=height*.22 and not any(_designation(row,group["box"])[1] for row in group["rows"])])
    projected = [group for group in groups if group not in roots]
    partial,_,_,missing = _project_graph_candidates(projected,edition_id,image_hash,width,height)
    unresolved.extend(missing)
    result["graph"] = None
    result["partial_graph"] = partial
    # Being assigned to a mistaken row/category must not remove an observed
    # word from the explicit root-repair contract.
    result["bootstrap_words"] = [{"id":item["id"],"text":item["text"],"region":item["region"]}
        for item in observations if item["kind"]=="ocr_word"]
    result["projection"] = {"method":"cached_observation_partial_projection","version":RASTER_VERSION,
        "source_extraction_version":extracted.get("version"),"ocr_invocations":0,"cv_invocations":0}
    result["coverage_established"] = False
    return result


def extract_raster_chart(image_path, edition_id, *, ocr_engine="tesseract", language="eng", psm=11,
                         min_confidence=20.0, timeout_s=120, dictionary=None):
    """Extract unreviewed rectangular-chart candidates from this image alone.

    Headings are the first OCR row in each box. A unique compact box without a
    designation-bearing row is the root candidate; ambiguity returns graph=None.
    Rows without a visible designation stay unresolved observations. This style
    assumption is explicit and does not establish general other-figure support.
    """
    if ocr_engine!="tesseract":
        raise ValueError("RASTER_OCR_ENGINE_UNSUPPORTED")
    if not isinstance(edition_id,str) or not edition_id.strip():
        raise ValueError("RASTER_EDITION_REQUIRED")
    dictionary_entries = _dictionary_entries(dictionary, edition_id)
    if not isinstance(psm,int) or not 0<=psm<=13 or not 0<=min_confidence<=100 or timeout_s<=0:
        raise ValueError("RASTER_CONFIGURATION_INVALID")
    path = Path(image_path)
    payload = path.read_bytes()
    image_hash = hashlib.sha256(payload).hexdigest()
    import cv2
    import numpy as np
    image = cv2.imdecode(np.frombuffer(payload,dtype=np.uint8),cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("RASTER_IMAGE_UNREADABLE")
    height,width = image.shape[:2]
    engine = {"name":"tesseract","version":_engine_version(),"language":language,"psm":psm,
              "min_confidence":min_confidence,"timeout_s":timeout_s,"cv2_version":cv2.__version__,
              "input_type":"raster_image","ocr_invocations":0}
    unresolved = []
    diagnostics = {"unresolved_visual_structures":unresolved,"assumptions":[
        "Separate closed rectangular boxes; first OCR row is the group heading.",
        "A unique compact uncoded box is the root candidate.",
        "Designations must appear in terminal parentheses or a separated right column.",
        "Indentation gives layout candidates only; no semantic subtype is admitted."]}
    result = {"graph":None,"observations":[],"diagnostics":diagnostics,"engine":"tesseract+opencv","engine_details":engine,
              "version":f"{RASTER_VERSION}; {engine['version']}; OpenCV {cv2.__version__}","coverage_established":False,
              "input":{"edition_id":edition_id,"image_sha256":image_hash,"width":width,"height":height}}
    if dictionary is not None:
        result["dictionary_assistance"] = {"schema_version": dictionary["schema_version"],
            "source": deepcopy(dictionary["source"]), "content_sha256": dictionary["content_sha256"],
            "qualification": "Native-derived vocabulary normalizes observed OCR names/codes only; no source geometry, relationships or accepted status transferred."}
        diagnostics["assumptions"].append("Dictionary-assisted label/code normalization; source relationships are independently observed candidates.")
    try:
        engine["ocr_invocations"] = 1
        tsv = _run_tesseract(path,language,psm,timeout_s)
    except (RuntimeError,subprocess.SubprocessError,OSError) as error:
        unresolved.append({"kind":"ocr_error","error_type":type(error).__name__,"message":str(error)[:400]})
        return result
    if hashlib.sha256(path.read_bytes()).hexdigest()!=image_hash:
        raise ValueError("RASTER_INPUT_CHANGED_DURING_OCR")
    words,rejected = _words_from_tsv(tsv,width,height)
    diagnostics["rejected_tsv_words"] = rejected
    observations = result["observations"]

    def observe(kind, box, **fields):
        identifier = _identifier(edition_id,image_hash,kind,f"{box}|{fields}")
        item = {"id":identifier,"kind":kind,"edition_id":edition_id,"image_sha256":image_hash,
                "pixel_bbox":list(box),"region":_region(box,width,height),"verification":"candidate",**fields}
        observations.append(item)
        return identifier

    for word in words:
        word["observation_id"] = observe("ocr_word",word["pixel_bbox"],text=word["text"],confidence=word["confidence"],
            tsv_row_index=word["tsv_row_index"])
    usable = [word for word in words if word["confidence"]>=min_confidence]
    low = [word["observation_id"] for word in words if word["confidence"]<min_confidence]
    if low:
        unresolved.append({"kind":"low_confidence_ocr","observation_ids":low})
    boxes,lines = (_rectangles(image, repair_border_gaps=True) if dictionary is not None else _rectangles(image))
    groups = []
    assigned = set()
    for index,box in enumerate(boxes):
        members = [word for word in usable if _contains(box,word["pixel_bbox"],margin=2)]
        rows = _rows(members)
        rectangle_id = observe("visual_rectangle",box,method="opencv_line_morphology")
        for row in rows:
            row["observation_id"] = observe("ocr_row",row["pixel_bbox"],text=row["text"],confidence=row["confidence"],
                word_observation_ids=[word["observation_id"] for word in row["words"]])
            if dictionary_entries is not None:
                _normalize_observed_row(row, dictionary_entries)
            assigned.update(word["observation_id"] for word in row["words"])
        group = {"index":index,"box":box,"rows":rows,"rectangle_id":rectangle_id}
        if dictionary_entries is not None:
            _assisted_group_identity(group, dictionary_entries)
        groups.append(group)
    diagnostics.update(ocr_word_count=len(words),usable_word_count=len(usable),low_confidence_word_count=len(low),
                       rejected_word_count=len(rejected),rectangle_count=len(boxes))
    unassigned = [word["observation_id"] for word in usable if word["observation_id"] not in assigned]
    if unassigned:
        unresolved.append({"kind":"ocr_outside_detected_boxes","observation_ids":unassigned})
    if dictionary_entries is not None:
        roots = [group for group in groups if group.get("normalized_identity", {}).get("kind") == "root"]
        diagnostics["normalization"] = [{"observation_id": row["observation_id"], **row["normalization"]}
            for group in groups for row in group["rows"] if row.get("normalization")]
    else:
        roots = [group for group in groups if group["rows"] and len(group["rows"])<=2
            and group["box"][3]<=height*.22 and not any(_designation(row,group["box"])[1] for row in group["rows"])]
    if len(roots)!=1:
        unresolved.append({"kind":"root_box_not_unique","candidate_rectangle_ids":[group["rectangle_id"] for group in roots]})
        return rebuild_partial_from_observations(result, dictionary=dictionary)
    root = roots[0]
    graph,category_nodes,root_node,missing = _project_graph_candidates(groups,edition_id,image_hash,width,height,root)
    unresolved.extend(missing)
    linked_categories = set()
    for component in _connector_contacts(lines,boxes):
        if root["index"] not in component["box_indices"]:
            continue
        component_id = observe("visual_line_component",component["pixel_bbox"],
            rectangle_observation_ids=[groups[index]["rectangle_id"] for index in component["box_indices"]])
        for index in component["box_indices"]:
            if index in category_nodes and index not in linked_categories:
                category = category_nodes[index]
                graph["edges"].append({"from":root_node["id"],"to":category["id"],"type":"CHART_CONNECTOR",
                    "region":_region(component["pixel_bbox"],width,height),
                    "observation_ids":[root["rectangle_id"],groups[index]["rectangle_id"],component_id],"verification":"candidate"})
                linked_categories.add(index)
    for index,category in category_nodes.items():
        if index not in linked_categories:
            unresolved.append({"kind":"root_category_connector_unresolved","category_id":category["id"],
                               "root_id":root_node["id"]})
    result["graph"] = graph
    return result
