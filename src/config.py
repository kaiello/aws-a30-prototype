import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root or user home
load_dotenv(Path(__file__).resolve().parent.parent / ".env")
load_dotenv(Path.home() / ".env")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_PATH = DATA_DIR / "AWS_A3.0_2020.pdf"

PARSED_DIR = BASE_DIR / "parsed"
PARSED_TEXT_FILE = PARSED_DIR / "text_chunks.jsonl"
PARSED_TABLES_DIR = PARSED_DIR / "tables"
PARSED_FIGURES_DIR = PARSED_DIR / "figures"

STORAGE_DIR = BASE_DIR / "storage"
EVAL_DIR = BASE_DIR / "eval"
BENCHMARK_FILE = EVAL_DIR / "gold_benchmark.json"

# Ingestion configuration
FIGURE_RENDER_DPI = 180
ANNEX_B_START_PAGE = 93  # 0-indexed PDF page where Annex B starts
ANNEX_A_START_PAGE = 81  # 0-indexed PDF page where Annex A starts
GLOSSARY_START_PAGE = 18 # 0-indexed PDF page where Clause 4 starts

# Inference Configuration: Default to Google Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "models/text-embedding-004")

# Alternative local/cloud backends
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen3-vl:8b-instruct")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "qwen2.5:3b")
