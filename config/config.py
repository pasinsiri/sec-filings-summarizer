import os
from dotenv import load_dotenv

load_dotenv()

# Grok API Key
GROK_API_KEY = os.getenv("GROK_API_KEY")

# Choose model: "grok-3" (cheapest) or "grok-4" (best)
GROK_MODEL = "grok-3"  # or "grok-4" if you have access

# What filing type to summarize
FILING_TYPE = "10-Q"  # or "10-K"

# Max chunks per filing (controls cost vs quality)
MAX_CHUNKS = 10