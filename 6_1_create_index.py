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
        {"name": "code",       "type": "Edm.String", "key": True,  "filterable": True, "sortable": True},
        {"name": "title_tr",   "type": "Edm.String", "searchable": True, "filterable": True,  "sortable": True},
        {"name": "title_en",   "type": "Edm.String", "searchable": True, "filterable": True,  "sortable": True},
        {"name": "category_tr","type": "Edm.String", "searchable": True, "filterable": True,  "facetable": True, "sortable": True},
        {"name": "category_en","type": "Edm.String", "searchable": True, "filterable": True,  "facetable": True, "sortable": True},
        {"name": "alias_tr",   "type": "Edm.String", "filterable": True},
        {"name": "alias_en",   "type": "Edm.String", "filterable": True},

        # Fund details
        {"name": "fund_name",              "type": "Edm.String", "searchable": True},
        {"name": "fund_code",              "type": "Edm.String", "filterable": True},
        {"name": "benchmark",              "type": "Edm.String", "searchable": True},
        {"name": "comparison_criteria",    "type": "Edm.String", "searchable": True},
        {"name": "ipo_date",               "type": "Edm.String", "filterable": True, "sortable": True},
        {"name": "taxation",               "type": "Edm.String", "searchable": True},
        {"name": "trading_rules",          "type": "Edm.String", "searchable": True},
        {"name": "annual_management_fee",  "type": "Edm.String", "filterable": True, "sortable": True},
        {"name": "investment_strategy",    "type": "Edm.String", "searchable": True},
        {"name": "investor_profile",       "type": "Edm.String", "searchable": True},

        # Recommendation
        {"name": "recommended",        "type": "Edm.Boolean", "filterable": True},
        {"name": "recommendation_date", "type": "Edm.String",  "filterable": True, "sortable": True},

        # Latest price snapshot (flattened from Price History[0])
        {"name": "latest_price",            "type": "Edm.Double",  "filterable": True, "sortable": True},
        {"name": "latest_price_date",       "type": "Edm.String",  "filterable": True, "sortable": True},
        {"name": "total_shares",            "type": "Edm.Double",  "filterable": True, "sortable": True},
        {"name": "investor_count",          "type": "Edm.Double",  "filterable": True, "sortable": True},
        {"name": "portfolio_size",          "type": "Edm.Double",  "filterable": True, "sortable": True},

        # Full price history stored as JSON string for retrieval
        {"name": "price_history_json",  "type": "Edm.String", "searchable": False, "retrievable": True},
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
                        {"fieldName": "trading_rules"},
                    ],
                    "prioritizedKeywordsFields": [
                        {"fieldName": "category_tr"},
                        {"fieldName": "category_en"},
                        {"fieldName": "fund_name"},
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
    price_history = fund.get("Price History", [])
    latest = price_history[0] if price_history else {}

    return {
        "@search.action": "mergeOrUpload",
        "code":                fund.get("code", ""),
        "title_tr":            fund.get("title_tr", ""),
        "title_en":            fund.get("title_en", ""),
        "category_tr":         fund.get("category_tr", ""),
        "category_en":         fund.get("category_en", ""),
        "alias_tr":            fund.get("alias_tr", ""),
        "alias_en":            fund.get("alias_en", ""),
        "fund_name":           fund.get("Fon Adı", ""),
        "fund_code":           fund.get("Fon Kodu", ""),
        "benchmark":           fund.get("Fonun Eşik Değeri", ""),
        "comparison_criteria": fund.get("Fonun Karşılaştırma Ölçütü", ""),
        "ipo_date":            fund.get("Fonun Halka Arz Tarihi", ""),
        "taxation":            fund.get("Vergilendirme", ""),
        "trading_rules":       fund.get("Alım Satım Esasları", ""),
        "annual_management_fee": fund.get("Yıllık Fon Yönetim Ücreti", ""),
        "investment_strategy": fund.get("Yatırım Stratejisi", ""),
        "investor_profile":    fund.get("Yatırımcı Profili", ""),
        "recommended":         fund.get("Recommended", False),
        "recommendation_date": fund.get("Recommendation Date", ""),
        # Latest price snapshot
        "latest_price":        latest.get("FIYAT"),
        "latest_price_date":   latest.get("TARIH", ""),
        "total_shares":        latest.get("TEDPAYSAYISI"),
        "investor_count":      latest.get("KISISAYISI"),
        "portfolio_size":      latest.get("PORTFOYBUYUKLUK"),
        # Full history as JSON string
        "price_history_json":  json.dumps(price_history, ensure_ascii=False),
    }


# ── Step 1: Create or Update the Index ───────────────────────────────────────
def create_or_update_index():
    url = f"{SEARCH_ENDPOINT}/indexes/{INDEX_NAME}?api-version={API_VERSION}"
    resp = requests.put(url, headers=HEADERS, json=INDEX_DEFINITION)
    if resp.status_code in (200, 201):
        print(f"✅ Index '{INDEX_NAME}' created/updated successfully.")
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
