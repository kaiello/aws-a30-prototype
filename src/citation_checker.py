"""
citation_checker.py: Deterministic citation validation and abstention verification
for AWS A3.0M/A3.0:2020.
"""

import re
from typing import Dict, Any, List

# Known ground truth elements in AWS A3.0
VALID_CLAUSES = ["Clause 1", "Clause 2", "Clause 3", "Clause 4", "Annex A", "Annex B", "Annex C"]
VALID_TABLES = ["Table A1", "Table A2", "Table A3", "Table A4", "Table A5"]
VALID_FIGURES = [f"Figure A{i}" for i in range(1, 7)] + [f"Figure B{i}" for i in range(1, 98)]

ABSTENTION_PHRASES = [
    "not specified",
    "not provided",
    "out of scope",
    "not covered",
    "does not contain",
    "abstain",
    "definitions only",
    "refer to aws d1.1",
    "refer to aws a5.1",
    "not mentioned"
]

def check_abstention(response_text: str) -> bool:
    """Returns True if the response properly abstained."""
    lowered = response_text.lower()
    return any(phrase in lowered for phrase in ABSTENTION_PHRASES)

def extract_citations(response_text: str) -> Dict[str, Any]:
    """Extracts cited clauses, tables, figures, and pages from response."""
    cited_clauses = [c for c in VALID_CLAUSES if c.lower() in response_text.lower()]
    cited_tables = [t for t in VALID_TABLES if t.lower() in response_text.lower()]
    
    # Extract figures (e.g., Figure A6, Figure B4, Figure B20)
    fig_matches = re.findall(r'Figure\s+[AB]\d+', response_text, re.IGNORECASE)
    cited_figures = list(set([re.sub(r'\s+', ' ', f.title()) for f in fig_matches]))
    
    # Extract page references
    page_matches = re.findall(r'(?:page|p\.)\s*(\d+)', response_text, re.IGNORECASE)
    cited_pages = [int(p) for p in page_matches]
    
    return {
        "has_citation": bool(cited_clauses or cited_tables or cited_figures or cited_pages),
        "clauses": cited_clauses,
        "tables": cited_tables,
        "figures": cited_figures,
        "pages": cited_pages
    }

def verify_response(query_item: Dict[str, Any], response_text: str) -> Dict[str, Any]:
    """Verifies a generated response against a benchmark query item."""
    must_abstain = query_item.get("must_abstain", False)
    did_abstain = check_abstention(response_text)
    
    citations = extract_citations(response_text)
    
    # Keyword check
    expected_keywords = query_item.get("expected_answer_keywords", [])
    found_keywords = [kw for kw in expected_keywords if kw.lower() in response_text.lower()]
    keyword_pass = len(found_keywords) >= max(1, len(expected_keywords) // 2)

    if must_abstain:
        is_pass = did_abstain
        reason = "Successfully abstained on out-of-scope query" if did_abstain else "Failed to abstain: hallucinated or answered out-of-scope query"
    else:
        # For answerable queries: must not falsely abstain, must hit key concepts, and must cite source
        gold_cit = query_item.get("gold_citation", {})
        cit_match = False
        if gold_cit:
            target_el = gold_cit.get("element_id", "")
            if target_el:
                cit_match = (target_el.lower() in response_text.lower())
        
        is_pass = (not did_abstain) and keyword_pass and (citations["has_citation"] or cit_match)
        reason = "Supported answer with valid citations" if is_pass else "Missing required citations or key technical content"

    return {
        "id": query_item.get("id"),
        "pass": is_pass,
        "did_abstain": did_abstain,
        "citations": citations,
        "keywords_found": found_keywords,
        "reason": reason
    }
