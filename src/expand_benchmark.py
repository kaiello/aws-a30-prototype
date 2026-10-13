"""
expand_benchmark.py: Combines original Q01-Q30 with new Q31-Q50 to produce
the complete 50-question gold evaluation benchmark for AWS A3.0M/A3.0:2020.
"""

import json
from pathlib import Path

BENCHMARK_PATH = Path("eval/gold_benchmark.json")

with open(BENCHMARK_PATH, "r", encoding="utf-8") as f:
    existing = json.load(f)

# Take exactly the first 30
base_30 = existing[:30]

new_20 = [
  {
    "id": "Q31",
    "modality": "figure",
    "query": "In Figure B16A, what are the inclination of axis and rotation of face coordinate limits for Flat position groove welds in plate?",
    "expected_answer_keywords": ["0° to 15°", "150° to 210°", "Flat", "Figure B16A"],
    "required_qualifiers": ["Figure B16A"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 102,
      "element_type": "figure",
      "element_id": "Figure B16A"
    },
    "must_abstain": False
  },
  {
    "id": "Q32",
    "modality": "figure",
    "query": "In Figure B23(J), what is the distinction between a toe temper bead and surface temper weld reinforcing beads?",
    "expected_answer_keywords": ["toe temper bead", "surface temper", "reinforcing", "base metal", "Figure B23"],
    "required_qualifiers": ["Figure B23"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 116,
      "element_type": "figure",
      "element_id": "Figure B23"
    },
    "must_abstain": False
  },
  {
    "id": "Q33",
    "modality": "figure",
    "query": "What are the callout components and features identified on Figure B46 for the Friction Stir Welding (FSW) process?",
    "expected_answer_keywords": ["tool shoulder", "probe", "advancing side", "retreating side", "exit hole", "Figure B46"],
    "required_qualifiers": ["Figure B46"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 150,
      "element_type": "figure",
      "element_id": "Figure B46"
    },
    "must_abstain": False
  },
  {
    "id": "Q34",
    "modality": "figure",
    "query": "What is the operational sequence discriminator between a starting weld tab and a runoff weld tab in Figure B12?",
    "expected_answer_keywords": ["starting weld tab", "runoff weld tab", "start", "end", "Figure B12"],
    "required_qualifiers": ["Figure B12"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 98,
      "element_type": "figure",
      "element_id": "Figure B12"
    },
    "must_abstain": False
  },
  {
    "id": "Q35",
    "modality": "figure",
    "query": "What are the three distinct oxyacetylene flame types illustrated in Figure B40?",
    "expected_answer_keywords": ["neutral flame", "oxidizing flame", "carburizing flame", "reducing flame", "Figure B40"],
    "required_qualifiers": ["Figure B40"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 145,
      "element_type": "figure",
      "element_id": "Figure B40"
    },
    "must_abstain": False
  },
  {
    "id": "Q36",
    "modality": "figure",
    "query": "What are the metal transfer modes illustrated in Figure B39 for gas metal arc welding?",
    "expected_answer_keywords": ["spray transfer", "globular transfer", "pulsed spray", "short circuiting", "Figure B39"],
    "required_qualifiers": ["Figure B39"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 144,
      "element_type": "figure",
      "element_id": "Figure B39"
    },
    "must_abstain": False
  },
  {
    "id": "Q37",
    "modality": "figure",
    "query": "In Figures B28 and B29, what is the fundamental difference between complete fusion and incomplete fusion?",
    "expected_answer_keywords": ["complete fusion", "incomplete fusion", "joint root", "groove face", "Figure B28"],
    "required_qualifiers": ["Figure B28"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 131,
      "element_type": "figure",
      "element_id": "Figure B28"
    },
    "must_abstain": False
  },
  {
    "id": "Q38",
    "modality": "figure",
    "query": "Identify six distinct crack types classified by location in Figure B33.",
    "expected_answer_keywords": ["longitudinal crack", "transverse crack", "crater crack", "toe crack", "underbead crack", "HAZ crack", "Figure B33"],
    "required_qualifiers": ["Figure B33"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 139,
      "element_type": "figure",
      "element_id": "Figure B33"
    },
    "must_abstain": False
  },
  {
    "id": "Q39",
    "modality": "figure",
    "query": "What are the primary component callouts of a plasma arc torch shown in Figure B35?",
    "expected_answer_keywords": ["constricting nozzle", "orifice gas", "electrode", "shielding gas", "Figure B35"],
    "required_qualifiers": ["Figure B35"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 141,
      "element_type": "figure",
      "element_id": "Figure B35"
    },
    "must_abstain": False
  },
  {
    "id": "Q40",
    "modality": "figure",
    "query": "In Figure B41, what is drag in oxygen cutting, and how is it illustrated?",
    "expected_answer_keywords": ["drag", "offset", "entry", "exit", "cutting jet", "Figure B41"],
    "required_qualifiers": ["Figure B41"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 146,
      "element_type": "figure",
      "element_id": "Figure B41"
    },
    "must_abstain": False
  },
  {
    "id": "Q41",
    "modality": "figure",
    "query": "According to Figure B34, what is the electrical distinction between DCEP and DCEN polarity?",
    "expected_answer_keywords": ["DCEP", "DCEN", "positive", "negative", "electrode", "workpiece", "Figure B34"],
    "required_qualifiers": ["Figure B34"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 140,
      "element_type": "figure",
      "element_id": "Figure B34"
    },
    "must_abstain": False
  },
  {
    "id": "Q42",
    "modality": "figure",
    "query": "In Figure B51, what are the primary stages and parameters shown for a typical flash welding cycle?",
    "expected_answer_keywords": ["preheat", "flashing", "upset", "platen spacing", "Figure B51"],
    "required_qualifiers": ["Figure B51"],
    "gold_citation": {
      "clause": "Annex B",
      "printed_page": 154,
      "element_type": "figure",
      "element_id": "Figure B51"
    },
    "must_abstain": False
  },
  {
    "id": "Q43",
    "modality": "text",
    "query": "According to Annex C1.5.3, why does the Definitions Subcommittee reject 'TIG' and 'MIG' in favor of GTAW and GMAW?",
    "expected_answer_keywords": ["inert", "active gas", "argon", "designation system", "Annex C"],
    "required_qualifiers": ["Annex C"],
    "gold_citation": {
      "clause": "Annex C",
      "printed_page": 161,
      "element_type": "text",
      "element_id": "Clause C1.5.3"
    },
    "must_abstain": False
  },
  {
    "id": "Q44",
    "modality": "text",
    "query": "Why was the term 'parallel joint' introduced in the 2020 edition to replace 'edge joint' according to Annex C1.5.7?",
    "expected_answer_keywords": ["parallel joint", "edge joint", "orientation", "five basic joint types", "Annex C"],
    "required_qualifiers": ["Annex C"],
    "gold_citation": {
      "clause": "Annex C",
      "printed_page": 162,
      "element_type": "text",
      "element_id": "Clause C1.5.7"
    },
    "must_abstain": False
  },
  {
    "id": "Q45",
    "modality": "table",
    "query": "According to Table D1, what new electrical terms were introduced in the 2020 edition for waveform-controlled welding?",
    "expected_answer_keywords": ["average instantaneous power", "AIP", "total instantaneous energy", "TIE", "Table D1"],
    "required_qualifiers": ["Table D1"],
    "gold_citation": {
      "clause": "Annex D",
      "printed_page": 165,
      "element_type": "table",
      "element_id": "Table D1"
    },
    "must_abstain": False
  },
  {
    "id": "Q46",
    "modality": "table",
    "query": "According to Table D4, which terms were revised from standard to nonstandard in the 2020 edition?",
    "expected_answer_keywords": ["cored solder", "penetration-enhancing flux", "multiple impulse welding", "Table D4"],
    "required_qualifiers": ["Table D4"],
    "gold_citation": {
      "clause": "Annex D",
      "printed_page": 170,
      "element_type": "table",
      "element_id": "Table D4"
    },
    "must_abstain": False
  },
  {
    "id": "Q47",
    "modality": "table",
    "query": "According to Table D6, name physical science and chemistry terms that were deleted in the 2020 edition.",
    "expected_answer_keywords": ["covalent bond", "ionic bond", "metal", "differential thermal expansion", "Table D6"],
    "required_qualifiers": ["Table D6"],
    "gold_citation": {
      "clause": "Annex D",
      "printed_page": 170,
      "element_type": "table",
      "element_id": "Table D6"
    },
    "must_abstain": False
  },
  {
    "id": "Q48",
    "modality": "text",
    "query": "What are the required format and submission procedures for requesting an official interpretation on an AWS standard in Annex F?",
    "expected_answer_keywords": ["standards@aws.org", "yes or no", "single provision", "proposed answer", "Annex F"],
    "required_qualifiers": ["Annex F"],
    "gold_citation": {
      "clause": "Annex F",
      "printed_page": 173,
      "element_type": "text",
      "element_id": "Clause F3"
    },
    "must_abstain": False
  },
  {
    "id": "Q49",
    "modality": "abstention",
    "query": "What is the recommended titanium laser welding shielding gas flow rate in Annex B?",
    "expected_answer_keywords": ["not specified", "out of scope", "abstain", "does not contain"],
    "required_qualifiers": [],
    "gold_citation": None,
    "must_abstain": True
  },
  {
    "id": "Q50",
    "modality": "abstention",
    "query": "Show me the friction stir welding parameter schedule on Figure B75.",
    "expected_answer_keywords": ["not specified", "does not exist", "out of scope", "B54", "does not contain"],
    "required_qualifiers": [],
    "gold_citation": None,
    "must_abstain": True
  }
]

combined = base_30 + new_20
with open(BENCHMARK_PATH, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)

print(f"Successfully assembled {len(combined)} questions into {BENCHMARK_PATH}")
