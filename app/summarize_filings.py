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
from ..functions.summarizer import chunk_text, summarize_with_grok

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

# ============================
# * Main processing
# ============================
def process_ticker(ticker, company_name):
    output_file = summaries_dir / f"{ticker}_{FILING_TYPE}_summary.md"
    if output_file.exists():
        print(f"Already done: {ticker}")
        return

    try:
        print(f"Fetching latest {FILING_TYPE} for {ticker} - {company_name}")
        filings = edgar.get_filings(ticker=ticker, form=FILING_TYPE)
        if filings.empty:
            print(f"No {FILING_TYPE} found for {ticker}")
            return

        latest = filings.iloc[0]
        doc = latest.document

        # Extract only useful items
        items = doc.get_items()
        useful_items = {}
        target_items = ["1", "1A", "1B", "2", "7", "7A", "8", "9A"]  # standard 10-K items

        for item in items:
            if item.item in target_items:
                text = item.text.strip()
                if len(text) > 200:  # skip empty
                    useful_items[item.item] = text

        if not useful_items:
            print(f"No useful text extracted for {ticker}")
            return

        # Chunk + summarize each section
        section_summaries = []
        total_cost_estimate = 0

        for item_num, text in useful_items.items():
            print(f"  Summarizing Item {item_num}...")
            chunks = chunk_text(text)
            item_summary = []

            for i, chunk in enumerate(chunks):
                summary = summarize_with_grok(chunk, client, is_final=False)
                item_summary.append(f"**Item {item_num} (part {i+1})**\n{summary}")
                # Rough cost estimate
                total_cost_estimate += (len(chunk) + len(summary)) / 4e6 * 3  # ~$3/M tokens

            section_summaries.append("\n\n".join(item_summary))

        # Final consolidation
        print(f"  Creating final consolidated summary for {ticker}...")
        combined = "\n\n---\n\n".join(section_summaries)
        final_summary = summarize_with_grok(combined, client, is_final=True)

        # Save result
        result = f"""# {FILING_TYPE} Summary: {ticker} - {company_name}

                **Filing Date**: {latest.filing_date.date()}  
                **Source**: SEC EDGAR  
                **Model**: {GROK_MODEL}  
                **Estimated Grok API cost**: ~${total_cost_estimate:.3f}

                --- 

                {final_summary}

                ---
                *Generated automatically using xAI Grok API + edgartools*
            """

        output_file.write_text(result, encoding="utf-8")
        print(f"Saved summary for {ticker} (cost ~${total_cost_estimate:.3f})")

        time.sleep(1)  # be nice to the API

    except Exception as e:
        print(f"Error with {ticker}: {e}")
        time.sleep(2)

