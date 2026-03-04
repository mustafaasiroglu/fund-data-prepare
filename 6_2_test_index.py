"""
Test script for querying the Azure AI Search funds_index via REST API.

Environment variables required:
  AZURE_SEARCH_ENDPOINT  – e.g. https://<service>.search.windows.net
  AZURE_SEARCH_API_KEY   – Admin or Query API key
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

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


default_fields = [
    "code",
    "title_tr",
    "title_en",
    "category_tr",
    "category_en",
    "first_offering_date",
    "annual_management_fee",
    "risk_level",
    "compare_measure",
    "taxation",
    "trading_terms",
    "investment_strategy",
    "investor_profile",
    "pdf_url",
    "recommended",
    "latest_price_close",
    "latest_price_date",
    "net_asset_value",
    "return_weekly",
    "return_one_month",
    "return_three_month",
    "return_six_month",
    "return_from_begin_of_year",
    "return_one_year",
    "return_three_year",
    "return_first_offering_date",
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
    results = search_funds("altın", top=5, fields=["code", "title_tr", "category_tr", "latest_price_close", "net_asset_value"])
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
    results = search_funds("döviz", top=5, fields=["code", "title_tr", "investment_strategy", "latest_price_close"])
    print(results)
