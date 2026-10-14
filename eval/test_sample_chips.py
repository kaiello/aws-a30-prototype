import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.query import run_query

test_chips = [
    ("Figure A1", "What processes are included under Solid-State Welding on Figure A1?"),
    ("Figure B1", "How does Figure B1 illustrate a butt joint configuration?"),
    ("Figure B21", "Which pipe welding test position in Figure B21 includes a restriction ring?"),
    ("Figure B25", "Identify the three distinct fillet weld throats illustrated in Figure B25"),
    ("Figure B46", "What are the callout components and features identified on Figure B46 for the Friction Stir Welding (FSW) process?")
]

print("="*70)
print("LIVE EVALUATION OF REPRESENTATIVE CHIPS ACROSS TECHNICAL GROUPS")
print("="*70)

for fig, q in test_chips:
    print(f"\n[QUERYING CHIP] {fig} -> '{q}'")
    res = run_query(q, mode="local")
    figs = [f["figure_id"] for f in res.get("resolved_figures", [])]
    tbls = [t["table_id"] for t in res.get("resolved_tables", [])]
    cits = res.get("citations", {})
    ans = res.get("answer", "")
    ep = res.get("epistemic_trace", {})
    ar = res.get("answer_route", {})
    
    first_sentence = ans.split("\n")[0] if ans else "No answer"
    print(f"  ✓ Answer ({len(ans)} chars): {first_sentence[:120]}...")
    print(f"  ✓ Multimodal Assets: Figures={figs}, Tables={tbls}")
    print(f"  ✓ Citations: Clauses={cits.get('clauses', [])}, Figures={cits.get('figures', [])}, Pages={cits.get('pages', [])}")
    print(f"  ✓ Epistemic Status: {ep.get('epistemic_status')} (Score: {ep.get('provenance_score', 0)*100:.0f}%)")
    print(f"  ✓ Answer Route: Target='{ar.get('concept_name')}', Recall={ar.get('evidence_recall_score', 0)*100:.0f}%, Group Items={len(ar.get('evidence_group', []))}")

print("\n" + "="*70)
print("LIVE SAMPLE CHIP EVALUATION COMPLETE: ALL RETURNED GROUNDED DATA")
print("="*70)
