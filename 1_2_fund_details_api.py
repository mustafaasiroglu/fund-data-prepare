import requests
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "fund_list.json")

# read fund list to get codes to query details for
with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
    fund_list = json.load(f)


headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Last date with data
url = "https://www.garantibbvaportfoy.com.tr/webservice/lastdate"
response = requests.post(url, headers=headers)
#response = "2026-03-02"
latest_date = response.text.strip('"')

for fund in fund_list:
    
    code = fund["code"]

    # Key Values
    url = "https://www.garantibbvaportfoy.com.tr/webservice/funddailyvalues"
    payload = {"lang":"tr","code":code,"date":latest_date,"rollBack":"T"}
    response = requests.post(url, json=payload, headers=headers)
    
    print("Fund:", code)
    data = json.loads(response.text)
    #convert to dict if it's a string
    if isinstance(data, str):
        data = json.loads(data)
    keyvalues = data.get("data", {})
    keyvalues["FirstDate"] = keyvalues["FirstDate"].split("T")[0] if "FirstDate" in keyvalues else ""

    # Getiri
    url = "https://www.garantibbvaportfoy.com.tr/webservice/funddailyrateofchangeall"
    payload = {"lang":"tr","code":code,"rollBack":"T"}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    # API may return a JSON-encoded string; parse again if needed
    if isinstance(data, str):
        data = json.loads(data)
    #sample = {"data": {"Code": "GZJ", "Weekly": -0.335619, "OneMonth": 2.898833, "ThreeMonth": 16.509587, "SixMonth": 26.475386, "FRomBeginOfYear": 12.816688, "OneYear": 53.855594, "ThreeYear": 302.07946, "FirstOfferingDate": 722.6594}}
    data = data.get("data", {})
    getiri = {k: v for k, v in data.items() if k != "Code"}

    # Distribution
    url = "https://www.garantibbvaportfoy.com.tr/webservice/portfoliodistributions"
    params = {"code": code, "lang": "tr"}
    response = requests.post(url, params=params, headers=headers)
    #response text = "{\"data\":{\"Id\":\"GTA54\",\"Data\":[{\"Name\":\"Mevduat (TL) (%)\",\"Percentage\":\"0.94\"},{\"Name\":\"Vadeli İşlemler Nakit Teminatları (%)\",\"Percentage\":\"4.53\"},{\"Name\":\"Para Piyasaları (%)\",\"Percentage\":\"0.01\"},{\"Name\":\"Yatırım Fonları Katılma Payları (%)\",\"Percentage\":\"2.73\"},{\"Name\":\"Kıymetli Maden (%)\",\"Percentage\":\"45.61\"},{\"Name\":\"Kıymetli Madenler Cinsinden BYF (%)\",\"Percentage\":\"9.7\"},{\"Name\":\"Kıymetli Madenler Cinsinden İhraç Edilen Kamu Kira Sertifikaları (%)\",\"Percentage\":\"34.3\"},{\"Name\":\"Ters Repo (%)\",\"Percentage\":\"2.17\"}]}}"
    data = response.json()
    if isinstance(data, str):
        data = json.loads(data)
    distribution = data.get("data", {}).get("Data", [])
    distribution.sort(key=lambda x: float(x.get("Percentage", 0)), reverse=True)

    # Risk
    url = f"https://www.garantibbvaportfoy.com.tr/webservice/fundrateofchangedaily?code={code}&date={latest_date}"
    response = requests.post(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, str):
        data = json.loads(data)
    # sample: "{\"data\":{\"Code\":\"GTA\",\"Result\":4.6774667227571065,\"RiskLevel\":6}}"
    risk = data.get("data", {}).get("RiskLevel", None)

    
    # add to fund dict
    fund["first_offering_date"] = keyvalues.get("FirstDate", "")
    fund["annual_management_fee"] = keyvalues.get("ManagementFeeAnnual", "")
    fund["latest_price_close"] = keyvalues.get("Close", "")
    fund["latest_price_date"] = latest_date
    fund["net_asset_value"] = keyvalues.get("NetAssetValue", "")
    fund["distribution"] = distribution
    fund["returns"] = getiri
    fund["risk_level"] = str(risk) + " / 7"
    
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(fund_list, f, ensure_ascii=False, indent=2)


