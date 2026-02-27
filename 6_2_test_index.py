"""
Test script for querying the Azure AI Search funds_index via REST API.

Environment variables required:
  AZURE_SEARCH_ENDPOINT  – e.g. https://<service>.search.windows.net
  AZURE_SEARCH_API_KEY   – Admin or Query API key
"""

import os
import json
import requests

# ── Configuration ────────────────────────────────────────────────────────────
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = "funds_index"
API_VERSION = "2024-07-01"

if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
    raise ValueError("Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY environment variables.")

HEADERS = {
    "Content-Type": "application/json",
    "api-key": SEARCH_API_KEY,
}


default_fields = ["fund_name", 
                       "fund_code",
                       "benchmark",
                       "comparison_criteria",
                       "ipo_date",
                       "taxation",
                       "trading_rules",
                       "annual_management_fee",
                        "investment_strategy",
                        "investor_profile",
                        "latest_price",
                        "latest_price_date",
                        "total_shares",
                        "investor_count",
                       "portfolio_size",
                       "recommended",
                       "recommendation_date",
                       ]

def search_funds(query: str, search_fields: list[str] = None, top: int = 5, filters: str = None, fields: list[str] = default_fields) -> list[dict]:
    """
    Search the funds_index.

    Args:
        query:   Search text (e.g. "hisse senedi", "altın fonu").
        search_fields: List of fields to search in. None = all fields.
        top:     Max number of results to return.
        filters: OData $filter expression (e.g. "recommended eq true", "category_tr eq 'Fon Sepeti Fonları'").
        fields:  List of fields to return. None = all fields.

    Returns:
        List of matching documents.
    """
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/search?api-version={API_VERSION}"

    body = {
        "search": query,
        "top": top,
        "count": True,
    }

    if filters:
        body["filter"] = filters
    if fields:
        body["select"] = ",".join(fields)
    if search_fields:
        body["searchFields"] = ",".join(search_fields)

    resp = requests.post(url, headers=HEADERS, json=body)
    resp.raise_for_status()

    data = resp.json()
    total = data.get("@odata.count", "?")
    results = data.get("value", [])

    print(f"🔍 Query: \"{query}\" | Filter: {filters or 'none'} | Total matches: {total} | Returned: {len(results)}")
    return results


# ── Test Cases ───────────────────────────────────────────────────────────────
if __name__ == "__main__":

   
    # Test 1: Full-text search
    print("\n" + "=" * 60)
    print("TEST 1: Full-text search – 'hisse senedi'")
    print("=" * 60)
    results = search_funds("hisse senedi", top=5)
    print(results)

    # Test 2: Filter only recommended funds
    print("\n" + "=" * 60)
    print("TEST 2: Filter – recommended funds only")
    print("=" * 60)
    results = search_funds("*", top=10, filters="recommended eq true")
    print(results)

    # Test 3: Search with specific fields
    print("\n" + "=" * 60)
    print("TEST 3: Select specific fields – 'altın'")
    print("=" * 60)
    results = search_funds("altın", top=5, fields=["fund_code", "fund_name", "category_tr", "latest_price", "portfolio_size"])
    print(results)

    # Test 4: Filter by category
    print("\n" + "=" * 60)
    print("TEST 4: Filter by category – Fon Sepeti Fonları")
    print("=" * 60)
    results = search_funds("*", top=10, filters="category_tr eq 'Fon Sepeti Fonları'")
    print(results)

    # Test 5: Search investment strategy
    print("\n" + "=" * 60)
    print("TEST 5: Search investment strategy – 'döviz'")
    print("=" * 60)
    results = search_funds("döviz", top=5, fields=["fund_code", "fund_name", "investment_strategy", "latest_price"])
    print(results)
