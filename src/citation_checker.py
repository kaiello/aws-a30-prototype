"""
citation_checker.py: Deterministic citation validation and abstention verification
for AWS A3.0M/A3.0:2020.
"""

import re
from typing import Dict, Any, List

# Known ground truth elements in AWS A3.0
VALID_CLAUSES = ["Clause 1", "Clause 2", "Clause 3", "Clause 4", "Annex A", "Annex B", "Annex C", "Annex D", "Annex E", "Annex F"]
VALID_TABLES = ["Table A1", "Table A2", "Table A3", "Table A4", "Table A5", "Table D1", "Table D2", "Table D3", "Table D4", "Table D5", "Table D6"]
VALID_FIGURES = [f"Figure A{i}" for i in range(1, 7)] + [f"Figure B{i}" for i in range(1, 98)]

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
    """Extracts cited clauses, tables, figures, and pages from response."""
    if not response_text:
        return {
            "has_citation": False,
            "clauses": [],
            "tables": [],
            "figures": [],
            "pages": []
        }
    text = str(response_text)
    cited_clauses = [c for c in VALID_CLAUSES if c.lower() in text.lower()]
    cited_tables = [t for t in VALID_TABLES if t.lower() in text.lower()]
    
    # Extract figures (e.g., Figure A6, Figure B4, Figure B16A, Figure B20)
    fig_matches = re.findall(r'Figure\s+[AB]\d+[A-Z]?', text, re.IGNORECASE)
    cited_figures = list(set([re.sub(r'\s+', ' ', f.title()) for f in fig_matches]))
    
    # Extract page references
    page_matches = re.findall(r'(?:page|p\.)\s*(\d+)', text, re.IGNORECASE)
    cited_pages = [int(p) for p in page_matches]
    
    return {
        "has_citation": bool(cited_clauses or cited_tables or cited_figures or cited_pages),
        "clauses": cited_clauses,
        "tables": cited_tables,
        "figures": cited_figures,
        "pages": cited_pages
    }

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
                cits = re.findall(r'\[\d+\]|\(Clause\s+\d+.*?\)|(?:Figure|Table)\s+[AB]\d+|p\.\s*\d+', clean_text, re.IGNORECASE)
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
        
        if not qualifier_pass:
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
