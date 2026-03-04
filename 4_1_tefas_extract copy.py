import datetime
import html
import json
import os
import time
import requests

DAYS_TO_FETCH = 60
DELAY_BETWEEN_REQUESTS = 5  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 10  # seconds

end_date = datetime.datetime.now().strftime("%d.%m.%Y")
start_date = (datetime.datetime.now() - datetime.timedelta(days=DAYS_TO_FETCH)).strftime("%d.%m.%Y")


output_folder = "funds_tefas_json"
os.makedirs(output_folder, exist_ok=True)

with open("fund_list.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(str(len(data)) + " funds found in fund_list.json")

for fund in data:
    alias = fund.get("alias_tr")
    if not alias:
        print(f"No alias found for fund {fund['code']}, skipping")
        continue

    output_path = os.path.join(output_folder, f"{fund['code']}.json")
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f"Already exists: {fund['code']}, skipping")
        continue

    api_url = f"https://www.tefas.gov.tr/api/DB/BindHistoryInfo"

    # fontip=YAT&sfontur=&fonkod=GOL&fongrup=&bastarih=03.02.2026&bittarih=27.02.2026&fonturkod=&fonunvantip=&kurucukod=

    params = {
        "fontip": "YAT",
        "sfontur": "",
        "fonkod": fund["code"],
        "fongrup": "",
        "bastarih": start_date,
        "bittarih": end_date,
        "fonturkod": "",
        "fonunvantip": "",
        "kurucukod": ""
    }

    headers = {
        "Origin": "https://www.tefas.gov.tr",
        "Referer": "https://www.tefas.gov.tr/TarihselVeriler.aspx",
        "X-Requested-With": "XMLHttpRequest",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    for attempt in range(1, MAX_RETRIES + 1):
        res = requests.post(api_url, data=params, headers=headers)

        if res.status_code != 200:
            print(f"HTTP {res.status_code} for {alias}, attempt {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"All retries failed for {alias}, skipping")
                break

        try:
            result = res.json()
            data = result.get("data", [])
            cleaned_data = []
            if not data:
                print(f"No data found in TEFAS response for {alias}, attempt {attempt}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"All retries failed for {alias}, skipping")
                    break
            for item in data:
                cleaned_item = {}
                cleaned_item["TARIH"] = datetime.datetime.fromtimestamp(int(item["TARIH"]) / 1000).strftime("%d.%m.%Y")
                cleaned_item["FIYAT"] = item["FIYAT"]
                cleaned_item["TEDPAYSAYISI"] = item["TEDPAYSAYISI"]
                cleaned_item["KISISAYISI"] = item["KISISAYISI"]
                cleaned_item["PORTFOYBUYUKLUK"] = item["PORTFOYBUYUKLUK"]
                cleaned_data.append(cleaned_item)
        except requests.exceptions.JSONDecodeError:
            print(f"Invalid JSON response for {alias}, attempt {attempt}/{MAX_RETRIES}")
            if attempt < MAX_RETRIES:
                print(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
                continue
            else:
                print(f"All retries failed for {alias}, skipping")
                break

        #write to code.json
        with open(os.path.join(output_folder, f"{fund['code']}.json"), "w", encoding="utf-8") as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        print(f"Downloaded TEFAS data for {alias}")
        break

    time.sleep(DELAY_BETWEEN_REQUESTS)


