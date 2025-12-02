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

