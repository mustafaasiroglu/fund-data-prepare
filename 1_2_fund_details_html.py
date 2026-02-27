import json
import requests

output_folder = "funds_html"

with open("fund_list.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print(str(len(data)) + " funds found in fund_list.json")

#list alias of fund codes to download pdfs for
fund_aliases = [fund.get("alias_tr") for fund in data]

for alias in fund_aliases:  
    fund_detail_page = f"https://www.garantibbvaportfoy.com.tr/{alias}"
    html = requests.get(fund_detail_page).text
    
    with open(f"{output_folder}/{alias}.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Downloaded HTML for {alias}")