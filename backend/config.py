import os

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DOTENV_PATH = os.path.join(BASE_DIR, "..", ".env")

# Data files
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
FAVORITES_FILE = os.path.join(DATA_DIR, "favorites.json")
WARDROBE_FILE = os.path.join(DATA_DIR, "wardrobe.json")
TRENDS_FILE = os.path.join(DATA_DIR, "trends.json")

# Constants
REQUIRED_CATEGORIES = ["top", "bottom", "shoes", "accessory"]
WARDROBE_REQUIRED_CATEGORIES = ["top", "bottom", "shoes"]
DEFAULT_OCCASION = "casual"
DEFAULT_STYLE = "minimal"
DEFAULT_BUDGET = 5000
DEFAULT_OPENAI_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}