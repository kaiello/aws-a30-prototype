import os
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_DATASETS_OFFLINE"] = "1"
from pathlib import Path
from dotenv import load_dotenv
from src.standard_manifest import get_manifest

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PDF_PATH = BASE_DIR / get_manifest().document["pdf_relpath"]

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
ANNEX_B_START_PAGE = get_manifest().section("Annex B")["spans"][0]["start_pdf_index"]
ANNEX_B_END_PAGE = get_manifest().section("Annex B")["spans"][-1]["end_pdf_index"]
ANNEX_A_START_PAGE = get_manifest().section("Annex A")["spans"][0]["start_pdf_index"]
GLOSSARY_START_PAGE = get_manifest().section("Clause 4")["spans"][0]["start_pdf_index"]

# Inference Configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# High-Capacity BGE-Large Embedding (1024-dim, 512 context)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5")
EMBEDDING_DIM = 1024

# Cross-Encoder Reranker Configuration
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "true").lower() == "true"

# Google Gemini (Dual-engine alternative)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY", "")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DEFAULT_ENGINE = os.getenv("DEFAULT_ENGINE", "deepseek")

# Custom / OpenAI / Groq / OpenRouter / Ollama alternative
CUSTOM_API_KEY = os.getenv("CUSTOM_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
CUSTOM_BASE_URL = os.getenv("CUSTOM_BASE_URL", "https://api.openai.com/v1")
CUSTOM_MODEL = os.getenv("CUSTOM_MODEL", "gpt-4o-mini")

# Local Ollama (Optional alternative)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen3-vl:8b-instruct")

# Optional production UI origins; request bodies cannot change this allowlist.
ALLOWED_WEB_ORIGINS = tuple(value.strip() for value in os.getenv("A30_ALLOWED_ORIGINS", "").split(",") if value.strip())
