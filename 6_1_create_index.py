"""
6_1_create_index.py
Creates an Azure AI Search index and uploads fund documents from fund_list_enriched.json
using REST API (no SDK dependency).

Environment variables required:
  AZURE_SEARCH_ENDPOINT  – e.g. https://<service>.search.windows.net
  AZURE_SEARCH_API_KEY   – Admin API key
"""

import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# ── Configuration ────────────────────────────────────────────────────────────
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = "funds_index"
API_VERSION = "2024-07-01"
DATA_FILE = "fund_list_enriched.json"
BATCH_SIZE = 100  # Azure Search limit per batch

if not SEARCH_ENDPOINT or not SEARCH_API_KEY:
    raise ValueError("Set AZURE_SEARCH_ENDPOINT and AZURE_SEARCH_API_KEY environment variables.")

HEADERS = {
    "Content-Type": "application/json",
    "api-key": SEARCH_API_KEY,
}

# ── Index Schema ─────────────────────────────────────────────────────────────
INDEX_DEFINITION = {
    "name": INDEX_NAME,
    "fields": [
        # Key & identifiers
        {"name": "code",        "type": "Edm.String", "key": True,  "filterable": True, "sortable": True},
        {"name": "title_tr",    "type": "Edm.String", "searchable": True, "filterable": True,  "sortable": True},
        {"name": "title_en",    "type": "Edm.String", "searchable": True, "filterable": True,  "sortable": True},
        {"name": "category_tr", "type": "Edm.String", "searchable": True, "filterable": True,  "facetable": True, "sortable": True},
        {"name": "category_en", "type": "Edm.String", "searchable": True, "filterable": True,  "facetable": True, "sortable": True},
        {"name": "alias_tr",    "type": "Edm.String", "filterable": True},
        {"name": "alias_en",    "type": "Edm.String", "filterable": True},

        # Fund details
        {"name": "first_offering_date",    "type": "Edm.String",  "filterable": True, "sortable": True},
        {"name": "annual_management_fee",  "type": "Edm.Double",  "filterable": True, "sortable": True},
        {"name": "risk_level",             "type": "Edm.String",  "filterable": True, "facetable": True},
        {"name": "compare_measure",        "type": "Edm.String",  "searchable": True},
        {"name": "taxation",               "type": "Edm.String",  "searchable": True},
        {"name": "trading_terms",           "type": "Edm.String",  "searchable": True},
        {"name": "investment_strategy",     "type": "Edm.String",  "searchable": True},
        {"name": "investor_profile",        "type": "Edm.String",  "searchable": True},
        {"name": "pdf_url",                "type": "Edm.String",  "filterable": False, "retrievable": True},

        # Recommendation
        {"name": "is_recommended",  "type": "Edm.Boolean", "filterable": True},

        # Latest price & fund size
        {"name": "latest_price_close",  "type": "Edm.Double",  "filterable": True, "sortable": True},
        {"name": "latest_price_date",   "type": "Edm.String",  "filterable": True, "sortable": True},
        {"name": "net_asset_value",     "type": "Edm.Double",  "filterable": True, "sortable": True},

        # Distribution stored as JSON string
        {"name": "distribution_json",   "type": "Edm.String",  "searchable": False, "retrievable": True},

        # Returns (flattened)
        {"name": "return_weekly",              "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_one_month",           "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_three_month",          "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_six_month",            "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_from_begin_of_year",   "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_one_year",             "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_three_year",            "type": "Edm.Double", "filterable": True, "sortable": True},
        {"name": "return_first_offering_date",  "type": "Edm.Double", "filterable": True, "sortable": True},

        # Relevant Document URLs stored as JSON string
        {"name": "documents_json",  "type": "Edm.String", "searchable": False, "retrievable": True},
    ],
    "semantic": {
        "configurations": [
            {
                "name": "fund-semantic-config",
                "prioritizedFields": {
                    "titleField": {"fieldName": "title_tr"},
                    "prioritizedContentFields": [
                        {"fieldName": "investment_strategy"},
                        {"fieldName": "investor_profile"},
                        {"fieldName": "trading_terms"},
                    ],
                    "prioritizedKeywordsFields": [
                        {"fieldName": "category_tr"},
                        {"fieldName": "category_en"},
                        {"fieldName": "title_en"},
                    ],
                },
            }
        ],
        "defaultConfiguration": "fund-semantic-config",
    },
}


# ── Helper: map enriched JSON keys → index field names ───────────────────────
def transform_document(fund: dict) -> dict:
    """Convert a raw fund dict to the flat index document schema."""
    returns = fund.get("returns", {})

    return {
        "@search.action": "mergeOrUpload",
        # Identifiers
        "code":                fund.get("code", ""),
        "title_tr":            fund.get("title_tr", ""),
        "title_en":            fund.get("title_en", ""),
        "category_tr":         fund.get("category_tr", ""),
        "category_en":         fund.get("category_en", ""),
        "alias_tr":            fund.get("alias_tr", ""),
        "alias_en":            fund.get("alias_en", ""),
        # Fund details
        "first_offering_date":   fund.get("first_offering_date", ""),
        "annual_management_fee": fund.get("annual_management_fee"),
        "risk_level":            fund.get("risk_level", ""),
        "compare_measure":       fund.get("compare_measure", ""),
        "taxation":              fund.get("taxation", ""),
        "trading_terms":         fund.get("trading_terms", ""),
        "investment_strategy":   fund.get("investment_strategy", ""),
        "investor_profile":      fund.get("investor_profile", ""),
        "pdf_url":               fund.get("pdf_url", ""),
        # Recommendation
        "is_recommended":           fund.get("is_recommended", False),
        # Latest price & fund size
        "latest_price_close":    fund.get("latest_price_close"),
        "latest_price_date":     fund.get("latest_price_date", ""),
        "net_asset_value":       fund.get("net_asset_value"),
        # Distribution as JSON string
        "distribution_json":     json.dumps(fund.get("distribution", []), ensure_ascii=False),
        # Returns (flattened)
        "return_weekly":              returns.get("Weekly"),
        "return_one_month":           returns.get("OneMonth"),
        "return_three_month":         returns.get("ThreeMonth"),
        "return_six_month":           returns.get("SixMonth"),
        "return_from_begin_of_year":  returns.get("FRomBeginOfYear"),
        "return_one_year":            returns.get("OneYear"),
        "return_three_year":          returns.get("ThreeYear"),
        "return_first_offering_date": returns.get("FirstOfferingDate"),
        # Documents as JSON string
        "documents_json":        json.dumps(fund.get("documents", []), ensure_ascii=False),
    }


# ── Step 1: Delete existing index then create fresh ─────────────────────────
def create_or_update_index():
    # Delete if exists
    del_url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
    del_resp = requests.delete(del_url, headers=HEADERS)
    if del_resp.status_code in (204, 404):
        print(f"🗑️  Index '{INDEX_NAME}' deleted (or did not exist).")
    else:
        print(f"⚠️  Delete returned status {del_resp.status_code}: {del_resp.text}")

    # Create
    url = f"{SEARCH_ENDPOINT}/indexes?api-version={API_VERSION}"
    resp = requests.post(url, headers=HEADERS, json=INDEX_DEFINITION)
    if resp.status_code in (200, 201):
        print(f"✅ Index '{INDEX_NAME}' created successfully.")
    else:
        print(f"❌ Failed to create index. Status: {resp.status_code}")
        print(resp.text)
        resp.raise_for_status()


# ── Step 2: Upload Documents in Batches ──────────────────────────────────────
def upload_documents(documents: list[dict]):
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}/docs/index?api-version={API_VERSION}"
    total = len(documents)
    uploaded = 0

    for i in range(0, total, BATCH_SIZE):
        batch = documents[i : i + BATCH_SIZE]
        body = {"value": batch}
        resp = requests.post(url, headers=HEADERS, json=body)
        if resp.status_code in (200, 207):
            results = resp.json().get("value", [])
            success = sum(1 for r in results if r.get("status", False))
            failed = len(results) - success
            uploaded += success
            if failed:
                print(f"  ⚠️  Batch {i // BATCH_SIZE + 1}: {success} OK, {failed} failed")
                for r in results:
                    if not r.get("status", False):
                        print(f"      Key={r.get('key')} Error={r.get('errorMessage')}")
            else:
                print(f"  ✔ Batch {i // BATCH_SIZE + 1}: {success} documents indexed")
        else:
            print(f"  ❌ Batch {i // BATCH_SIZE + 1} failed. Status: {resp.status_code}")
            print(resp.text)

    print(f"\n✅ Upload complete: {uploaded}/{total} documents indexed.")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    # Load data
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        funds = json.load(f)
    print(f"📂 Loaded {len(funds)} funds from {DATA_FILE}")

    # Transform
    documents = [transform_document(fund) for fund in funds]

    # Create index
    create_or_update_index()
    time.sleep(2)  # brief pause for index to be ready

    # Upload
    upload_documents(documents)


if __name__ == "__main__":
    main()
