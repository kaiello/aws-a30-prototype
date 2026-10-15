"""
citation_checker.py: Deterministic citation validation and abstention verification
for AWS A3.0M/A3.0:2020.
"""

import re
from typing import Dict, Any, List

from src.standard_manifest import get_manifest, extract_references

# Compatibility constants projected from the one source inventory.
VALID_CLAUSES = list(get_manifest().labels("sections"))
VALID_TABLES = list(get_manifest().labels("tables"))
VALID_FIGURES = list(get_manifest().labels("figures"))

STRONG_ABSTENTION_PREFIXES = [
    "i don't have enough information",
    "i do not have enough information",
    "based on the provided context, i do not have enough information",
    "based on the provided context, i don't have enough information",
    "the provided context does not contain enough information",
    "the provided context does not contain any details",
    "the provided context does not contain information",
    "this query is out of scope",
    "out of scope",
    "this is out of scope",
    "not specified in aws a3.0",
    "not covered in aws a3.0",
    "aws a3.0 does not contain",
    "aws a3.0 does not specify",
    "aws a3.0 is a terms and definitions standard"
]

STRONG_ABSTENTION_SUBSTRINGS = [
    "out of scope",
    "outside the scope",
    "does not exist in aws a3.0",
    "does not exist in annex",
    "does not exist in table",
    "refer to aws d1.1",
    "refer to aws a5.1",
    "acceptance criteria are not covered",
    "not defined in aws a3.0",
    "is not defined in aws a3.0",
    "not included in aws a3.0"
]

def check_abstention(response_text: str) -> bool:
    """Returns True if the response properly abstained."""
    if not response_text:
        return False
    lowered = str(response_text).strip().lower()
    if any(lowered.startswith(p) for p in STRONG_ABSTENTION_PREFIXES):
        return True
    return any(p in lowered for p in STRONG_ABSTENTION_SUBSTRINGS)

def extract_citations(response_text: str) -> Dict[str, Any]:
    """Resolve canonical source IDs; unresolved tokens never count as exact citations."""
    text = str(response_text or "")
    result = extract_references(text)
    valid_pages = {int(p["printed_label"]) for p in get_manifest().document["pages"]
                   if p["printed_label"] and p["printed_label"].isdigit()}
    result["pages"] = list(dict.fromkeys(int(p) for p in re.findall(r"(?:page|p\.)\s*(\d+)", text, re.IGNORECASE) if int(p) in valid_pages))
    result["has_citation"] = bool(result["clauses"] or result["tables"] or result["figures"] or result["pages"])
    result["source_anchors"] = {label: get_manifest().source_anchors(label)
                                for key in ["clauses", "tables", "figures"] for label in result[key]}
    return result

def extract_grounded_claims(response_text: str) -> List[Dict[str, Any]]:
    """Extracts material claims and links each to its cited source anchors."""
    if not response_text:
        return []
    claims = []
    lines = [l.strip() for l in str(response_text).splitlines() if l.strip()]
    for line in lines:
        if (line.startswith(('*', '-', '•')) or re.match(r'^\d+\.', line) or '**' in line) and not line.startswith('#'):
            clean_text = re.sub(r'^[\*\-•\d\.\s]+', '', line).strip()
            if len(clean_text) > 15:
                # Find any bracketed or inline citations in this line
                refs = extract_references(clean_text)
                cits = list(dict.fromkeys([label for key in ["clauses", "figures", "tables"] for label in refs[key]]
                                         + re.findall(r'\[\d+\]|p\.\s*\d+', clean_text, re.IGNORECASE)))
                claims.append({
                    "claim": clean_text,
                    "anchors": cits if cits else ["Inferred from context"]
                })
    return claims

def verify_response(query_item: Dict[str, Any], response_text: str) -> Dict[str, Any]:
    """Verifies a generated response against a benchmark query item with adversarial safeguards."""
    resp_str = str(response_text or "")
    must_abstain = query_item.get("must_abstain", False)
    did_abstain = check_abstention(resp_str)
    
    citations = extract_citations(resp_str)
    grounded_claims = extract_grounded_claims(resp_str)
    
    # Keyword check
    expected_keywords = query_item.get("expected_answer_keywords", [])
    found_keywords = [kw for kw in expected_keywords if kw.lower() in resp_str.lower()]
    keyword_pass = len(found_keywords) >= max(1, len(expected_keywords) // 2)

    # Qualifier check
    required_qualifiers = query_item.get("required_qualifiers", [])
    missing_qualifiers = [q for q in required_qualifiers if q.lower() not in resp_str.lower()]
    qualifier_pass = (len(missing_qualifiers) == 0)

    if must_abstain:
        is_pass = did_abstain
        reason = "Successfully abstained on out-of-scope query" if did_abstain else "Failed to abstain: hallucinated or answered out-of-scope query"
    else:
        gold_cit = query_item.get("gold_citation", {})
        cit_match = False
        if gold_cit:
            target_el = gold_cit.get("element_id", "")
            if target_el:
                cit_match = (target_el.lower() in response_text.lower())
        
        if citations.get("unresolved_elements"):
            is_pass = False
            reason = "Unknown, ambiguous or unverified source citation"
        elif not qualifier_pass:
            is_pass = False
            reason = f"Omitted required qualifier(s): {missing_qualifiers}"
        elif did_abstain:
            is_pass = False
            reason = "False abstention on answerable query"
        elif not keyword_pass:
            is_pass = False
            reason = "Missing key technical concepts"
        elif not (citations["has_citation"] or cit_match):
            is_pass = False
            reason = "Missing required standard citation"
        else:
            is_pass = True
            reason = "Supported answer with valid citations and qualifiers"

    return {
        "id": query_item.get("id"),
        "pass": is_pass,
        "did_abstain": did_abstain,
        "citations": citations,
        "grounded_claims_count": len(grounded_claims),
        "keywords_found": found_keywords,
        "missing_qualifiers": missing_qualifiers,
        "reason": reason
    }
