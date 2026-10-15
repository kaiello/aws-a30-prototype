"""
test_pre_retrieval.py: Unit tests for Pre-Retrieval Intent Engine, Acronym Expansion,
and Out-of-Scope Early Abstention Gate.
"""

import sys
from pathlib import Path
import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.pre_retrieval import (
    check_early_abstention,
    expand_query,
    extract_referenced_elements,
    WELDING_ACRONYMS
)

def test_early_abstention_aws_d1_1():
    q = "What are the visual inspection acceptance criteria for AWS D1.1 fillet welds?"
    abstain = check_early_abstention(q)
    assert abstain is not None
    assert abstain["status"] == "TRUTHFUL_ABSTENTION"
    assert "aws d1.1" in abstain["reason"].lower()

def test_early_abstention_preheat():
    q = "What is the minimum preheat temperature schedule for 50mm plate?"
    abstain = check_early_abstention(q)
    assert abstain is not None
    assert abstain["status"] == "TRUTHFUL_ABSTENTION"

def test_in_scope_no_abstention():
    q = "What is the definition of complete joint penetration?"
    abstain = check_early_abstention(q)
    assert abstain is None

def test_acronym_expansion_gmaw():
    q = "Explain the advantages of GMAW over SMAW"
    expanded = expand_query(q)
    assert "GMAW" in expanded["matched_acronyms"]
    assert "SMAW" in expanded["matched_acronyms"]
    assert expanded["matched_acronyms"]["GMAW"] == "gas metal arc welding"
    assert "gas metal arc welding" in expanded["enriched_query"]

def test_acronym_expansion_test_positions():
    q = "What is the groove weld position for 6GR?"
    expanded = expand_query(q)
    assert "6GR" in expanded["matched_acronyms"]
    assert "6GR multiple position pipe" in expanded["matched_acronyms"]["6GR"]

def test_figure_extraction():
    q = "Show me fillet weld throat definitions on Figure B25 and Figure B12"
    refs = extract_referenced_elements(q)
    assert "Figure B25" in refs["figures"]
    assert "Figure B12" in refs["figures"]

def test_table_extraction():
    q = "List all processes classified under Table A1 and Table A5"
    refs = extract_referenced_elements(q)
    assert "Table A1" in refs["tables"]
    assert "Table A5" in refs["tables"]
