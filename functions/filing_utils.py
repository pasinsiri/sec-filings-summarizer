"""
Utility functions for working with SEC filings
"""
from edgar import Company, set_identity
from typing import List, Optional
import datetime


def get_filing_dates(ticker: str, form: str = "10-K", max_filings: Optional[int] = None) -> List[datetime.date]:
    """
    Get filing dates for a specific ticker and form type.

    Args:
        ticker: Stock ticker symbol (e.g., 'GOOGL', 'AAPL')
        form: Filing form type (default: '10-K', can also be '10-Q', '8-K', etc.)
        max_filings: Maximum number of filings to return (default: all available)

    Returns:
        List of filing dates, ordered from most recent to oldest

    Example:
        >>> dates = get_filing_dates('GOOGL', form='10-K', max_filings=5)
        >>> print(f"Latest filing: {dates[0]}")
        >>> print(f"Previous filing: {dates[1]}")
    """
    company = Company(ticker)
    filings = company.get_filings(form=form)

    if not filings or len(filings) == 0:
        return []

    # Use get_filing_at() to safely access filings
    total_filings = len(filings)
    num_to_get = min(max_filings, total_filings) if max_filings else total_filings

    filing_dates = []
    for i in range(num_to_get):
        filing = filings.get_filing_at(i)
        filing_dates.append(filing.filing_date)

    return filing_dates


def get_previous_filing_date(ticker: str, form: str = "10-K", offset: int = 1) -> Optional[datetime.date]:
    """
    Get the filing date of a previous filing.

    Args:
        ticker: Stock ticker symbol
        form: Filing form type (default: '10-K')
        offset: How many filings back to go (1 = previous, 2 = two filings ago, etc.)

    Returns:
        Filing date or None if not enough filings exist

    Example:
        >>> # Get the previous 10-K filing date
        >>> prev_date = get_previous_filing_date('GOOGL', form='10-K', offset=1)
        >>> print(f"Previous filing: {prev_date}")

        >>> # Get the filing from two years ago
        >>> two_years_ago = get_previous_filing_date('GOOGL', form='10-K', offset=2)
    """
    dates = get_filing_dates(ticker, form=form, max_filings=offset + 1)

    if len(dates) <= offset:
        return None

    return dates[offset]


def get_latest_filing_date(ticker: str, form: str = "10-K") -> Optional[datetime.date]:
    """
    Get the date of the most recent filing.

    Args:
        ticker: Stock ticker symbol
        form: Filing form type (default: '10-K')

    Returns:
        Filing date or None if no filings exist

    Example:
        >>> latest = get_latest_filing_date('GOOGL')
        >>> print(f"Latest 10-K: {latest}")
    """
    dates = get_filing_dates(ticker, form=form, max_filings=1)
    return dates[0] if dates else None


if __name__ == "__main__":
    # Example usage
    set_identity("Demo demo@example.com")

    ticker = "GOOGL"
    print(f"Filing dates for {ticker}:\n")

    # Get latest filing date
    latest = get_latest_filing_date(ticker)
    print(f"Latest 10-K filing:   {latest}")

    # Get previous filing date
    previous = get_previous_filing_date(ticker, offset=1)
    print(f"Previous 10-K filing: {previous}")

    # Get filing from 2 years ago
    two_years_ago = get_previous_filing_date(ticker, offset=2)
    print(f"2 filings ago:        {two_years_ago}")

    # Get all recent filing dates
    print(f"\nAll recent 10-K filings:")
    recent_dates = get_filing_dates(ticker, max_filings=5)
    for i, date in enumerate(recent_dates):
        print(f"  {i+1}. {date}")

    # Also works with other filing types
    print(f"\nLatest 10-Q filing: {get_latest_filing_date(ticker, form='10-Q')}")
