import requests
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE_RAW = os.path.join(SCRIPT_DIR, "fund_list_raw.json")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "fund_list.json")

url = "https://www.garantibbvaportfoy.com.tr/webservice/GetFundsByCategory"
params = {"lang": "tr"}

headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

try:
    response = requests.post(url, params=params, headers=headers)
    response.raise_for_status()

    data = response.json()

    # API may return a JSON-encoded string; parse again if needed
    if isinstance(data, str):
        data = json.loads(data)

    # Write response to JSON file
    with open(OUTPUT_FILE_RAW, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # prepare fund list output in following format
    # ============================================================
    # code
    # title_tr
    # title_en
    # category_tr
    # category_en
    # alias_tr
    # alias_en

    fund_list = []
    
    for category in data.get("data", []):
        category_tr = category["CategoryName"]["tr"]
        category_en = category["CategoryName"]["en"]
        category_id = category["CategoryId"]

        for fund in category.get("Funds", []):
            code = fund["Code"]["iv"]
            title_tr = fund["Title"]["tr"]
            title_en = fund["Title"]["en"]
            alias_tr = fund.get("Alias", {}).get("tr", "")
            alias_en = fund.get("Alias", {}).get("en", "")

            fund_list.append({
                "code": code,
                "title_tr": title_tr,
                "title_en": title_en,
                "category_tr": category_tr,
                "category_en": category_en,
                "alias_tr": alias_tr,
                "alias_en": alias_en
            })
    # Print fund list to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(fund_list, f, ensure_ascii=False, indent=2)

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except json.JSONDecodeError as e:
    print(f"Failed to parse JSON response: {e}")
except KeyError as e:
    print(f"Unexpected response structure, missing key: {e}")
