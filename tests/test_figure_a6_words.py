"""
test_figure_a6_words.py: Verifies that any word, branch, or designation on Figure A6
can be queried accurately with standard definitions and visual evidence resolution.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.query import run_query

sys.stdout.reconfigure(encoding="utf-8")

TEST_QUERIES = [
    "show me flame contact on figure A6",
    "What processes require Pressure normal to faying surfaces on Figure A6?",
    "What is EXB on Figure A6 and what are its physical characteristics?",
    "Which processes use Vacuum shielding on Figure A6?"
]

def main():
    print("Testing word-level queryability across Figure A6:\n")
    for q in TEST_QUERIES:
        print("="*75)
        print("QUERY:", q)
        print("="*75)
        res = run_query(q)
        print("ANSWER:\n", res["answer"][:400] + ("..." if len(res["answer"]) > 400 else ""))
        print("\nRESOLVED FIGURES:", [f["figure_id"] for f in res["resolved_figures"]])
        print("CITATIONS:", res["citations"])
        print("\n")

if __name__ == "__main__":
    main()
