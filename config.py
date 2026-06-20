# ─────────────────────────────────────────────
#  config.py  —  API keys, model config, constants
# ─────────────────────────────────────────────

GROQ_API_KEY  = "YOUR_GROQ_API_KEY_HERE"   # Replace with your Groq key
GROQ_MODEL    = "llama-3.3-70b-versatile"
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"

# FastF1 cache directory (created automatically)
FASTF1_CACHE_DIR = "fastf1_cache"

# How many past races to pull for recent form
RECENT_RACES_COUNT = 5

# LLM settings
MAX_TOKENS  = 1200
TEMPERATURE = 0.6

# Season to pull data from (update each year)
CURRENT_SEASON = 2024
