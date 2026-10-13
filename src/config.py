import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_PATH = DATA_DIR / "AWS_A3.0_2020.pdf"

PARSED_DIR = BASE_DIR / "parsed"
PARSED_TEXT_FILE = PARSED_DIR / "text_chunks.jsonl"
PARSED_TABLES_DIR = PARSED_DIR / "tables"
PARSED_FIGURES_DIR = PARSED_DIR / "figures"

PARSED_ANATOMY_DIR = PARSED_DIR / "figures_anatomy"

STORAGE_DIR = BASE_DIR / "storage"
EVAL_DIR = BASE_DIR / "eval"
BENCHMARK_FILE = EVAL_DIR / "gold_benchmark.json"

# Load environment
load_dotenv(BASE_DIR / ".env")
load_dotenv(Path.home() / ".env")

# Ingestion configuration
FIGURE_RENDER_DPI = 180
ANNEX_B_START_PAGE = 93  # 0-indexed PDF page where Annex B starts
ANNEX_A_START_PAGE = 81  # 0-indexed PDF page where Annex A starts
GLOSSARY_START_PAGE = 18 # 0-indexed PDF page where Clause 4 starts

# Inference Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# Local MiniLM Embedding
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
EMBEDDING_DIM = 384

# Google Gemini (Dual-engine alternative)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DEFAULT_ENGINE = os.getenv("DEFAULT_ENGINE", "deepseek")

# Local Ollama (Optional alternative)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen3-vl:8b-instruct")
