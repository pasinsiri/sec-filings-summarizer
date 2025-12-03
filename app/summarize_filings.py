import json
import sys
import time
import argparse
from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup
from edgar import Company, set_identity
from openai import OpenAI

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config import GROK_API_KEY, GROK_MODEL, FILING_TYPE, MAX_CHUNKS
from functions.summarizer import chunk_text, summarize_with_grok

# ============================
# Setup
# ============================
# Set SEC identity (required by SEC)
set_identity("Your Name your.email@example.com")

client = OpenAI(
    api_key=GROK_API_KEY,
    base_url="https://api.x.ai/v1"
)

summaries_dir = Path("output")
summaries_dir.mkdir(exist_ok=True)

# ============================
# * Main processing
# ============================
def clean_html_text(html_content):
    """Extract and clean text from HTML filing content."""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Get text and clean it
    text = soup.get_text()

    # Clean up whitespace
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = ' '.join(chunk for chunk in chunks if chunk)

    return text


def process_filing(ticker, company_name, filing, filing_index=None):
    """Process a single filing and generate summary."""
    filing_date = filing.filing_date

    # Create output filename with index if processing multiple filings
    if filing_index is not None:
        output_file = summaries_dir / f"{ticker}_{FILING_TYPE}_{filing_date}_{filing_index}_summary.md"
    else:
        output_file = summaries_dir / f"{ticker}_{FILING_TYPE}_summary.md"

    if output_file.exists():
        print(f"  Already done: {ticker} filing from {filing_date}")
        return True

    try:
        print(f"  Processing {FILING_TYPE} filed on {filing_date}")

        # Get the filing HTML content
        html_content = filing.html()

        # Clean and extract text
        full_text = clean_html_text(html_content)

        if len(full_text) < 1000:
            print(f"  Filing text too short, skipping")
            return False

        print(f"  Extracted {len(full_text):,} characters from filing")

        # Chunk the text for processing
        chunks = chunk_text(full_text)
        print(f"  Split into {len(chunks)} chunks for summarization")

        # Summarize each chunk
        chunk_summaries = []
        total_cost_estimate = 0

        for i, chunk in enumerate(chunks):
            print(f"  Summarizing chunk {i+1}/{len(chunks)}...")
            summary = summarize_with_grok(chunk, client, is_final=False)
            chunk_summaries.append(f"**Part {i+1}**\n{summary}")
            # Rough cost estimate
            total_cost_estimate += (len(chunk) + len(summary)) / 4e6 * 3  # ~$3/M tokens
            time.sleep(0.5)  # Rate limiting

        # Final consolidation
        print(f"  Creating final consolidated summary...")
        combined = "\n\n---\n\n".join(chunk_summaries)
        final_summary = summarize_with_grok(combined, client, is_final=True)

        # Save result
        result = f"""# {FILING_TYPE} Summary: {ticker} - {company_name}

**Filing Date**: {filing_date}
**Source**: SEC EDGAR
**Model**: {GROK_MODEL}
**Estimated Grok API cost**: ~${total_cost_estimate:.3f}

---

{final_summary}

---
*Generated automatically using xAI Grok API + edgar library*
"""

        output_file.write_text(result, encoding="utf-8")
        print(f"✓ Saved summary for {ticker} from {filing_date} (cost ~${total_cost_estimate:.3f})")

        time.sleep(1)  # be nice to the API
        return True

    except Exception as e:
        print(f"✗ Error processing {ticker} filing from {filing_date}: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(2)
        return False


def process_ticker(ticker, company_name, num_filings=1):
    """Process one or more filings for a ticker."""
    try:
        print(f"\nFetching {FILING_TYPE} filings for {ticker} - {company_name}")

        # Get company and its filings
        company = Company(ticker)
        filings = company.get_filings(form=FILING_TYPE)

        if not filings or len(filings) == 0:
            print(f"No {FILING_TYPE} found for {ticker}")
            return

        total_available = len(filings)
        num_to_process = min(num_filings, total_available)
        print(f"Found {total_available} filings, will process {num_to_process}")

        # Process each filing using get_filing_at() to avoid PyArrow iteration issues
        successful = 0
        for idx in range(num_to_process):
            filing = filings.get_filing_at(idx)
            filing_index = idx + 1 if num_filings > 1 else None
            if process_filing(ticker, company_name, filing, filing_index):
                successful += 1

        print(f"✓ Completed {successful}/{num_to_process} filings for {ticker}")

    except Exception as e:
        print(f"✗ Error with {ticker}: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(2)

# ============================
# * Run everything
# ============================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Summarize SEC filings using Grok API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process latest filing for all stocks in stocks.json
  python app/summarize_filings.py

  # Process latest 3 filings for all stocks
  python app/summarize_filings.py --num-filings 3
  python app/summarize_filings.py -n 3

  # Process latest 5 filings for all stocks
  python app/summarize_filings.py -n 5
        """
    )

    parser.add_argument(
        '-n', '--num-filings',
        type=int,
        default=1,
        metavar='N',
        help='Number of latest filings to process per ticker (default: 1)'
    )

    args = parser.parse_args()

    # Validate num_filings
    if args.num_filings < 1:
        parser.error("--num-filings must be at least 1")

    # Get the project root directory
    project_root = Path(__file__).parent.parent
    stocks_file = project_root / "meta" / "stocks.json"

    with open(stocks_file, "r") as f:
        stocks = json.load(f)

    filing_text = "filing" if args.num_filings == 1 else f"{args.num_filings} filings"
    print(f"Starting summarization for {len(stocks)} stocks (processing latest {filing_text} each) using {GROK_MODEL}...")
    print(f"Output directory: {summaries_dir.absolute()}\n")

    for ticker, name in tqdm(stocks.items(), desc="Overall progress"):
        process_ticker(ticker.upper(), name, num_filings=args.num_filings)

    print(f"\n{'='*60}")
    print(f"All done! Check the '{summaries_dir}/' folder.")
    print(f"{'='*60}")