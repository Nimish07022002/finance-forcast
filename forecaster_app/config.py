import os
from dotenv import load_dotenv

# Load environment variables (for local setup)
load_dotenv()

# --- API Configuration ---
# In a real environment, API_KEY would be loaded from os.environ or a secret manager.
API_KEY = os.environ.get("GEMINI_API_KEY") or ""
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"

# --- Database Configuration ---
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "tcs_agent_db",
}
