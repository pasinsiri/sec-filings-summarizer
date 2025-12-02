import json
import os
import time
from pathlib import Path
from tqdm import tqdm
import requests
from bs4 import BeautifulSoup
from edgartools import EDGAR
from openai import OpenAI
from config import GROK_API_KEY, GROK_MODEL, FILING_TYPE, MAX_CHUNKS

# ============================
# Setup
# ============================
client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

summaries_dir = Path("output")
summaries_dir.mkdir(exist_ok=True)

edgar = EDGAR()

