import datetime
import html
import json
import os
import time
import requests

with open("fund_list.json", "r", encoding="utf-8") as f:
    fund_list = json.load(f)

enriched_fund_list = []

for fund in fund_list:
    alias = fund.get("alias_tr")
    if not alias:
        print(f"No alias found for fund {fund['code']}, skipping")
        continue

    #find pdf json for this fund
    pdf_json_path = os.path.join("funds_pdf_json", f"{fund['code']}.json")
    if os.path.exists(pdf_json_path) and os.path.getsize(pdf_json_path) > 0:
        with open(pdf_json_path, "r", encoding="utf-8") as f:
            pdf_data = json.load(f)

            fund["Fon Adı"] = pdf_data.get("Fon Adı", "")
            fund["Fon Kodu"] = pdf_data.get("Fon Kodu", "")
            fund["Fonun Eşik Değeri"] = pdf_data.get("Fonun Eşik Değeri", "")
            fund["Fonun Karşılaştırma Ölçütü"] = pdf_data.get("Fonun Karşılaştırma Ölçütü", "")
            fund["Fonun Halka Arz Tarihi"] = pdf_data.get("Fonun Halka Arz Tarihi", "")
            fund["Vergilendirme"] = pdf_data.get("Vergilendirme", "")
            fund["Alım Satım Esasları"] = pdf_data.get("Alım Satım Esasları", "")
            fund["Yıllık Fon Yönetim Ücreti"] = pdf_data.get("Yıllık Fon Yönetim Ücreti", "")
            fund["Yatırım Stratejisi"] = pdf_data.get("Yatırım Stratejisi", "")
            fund["Yatırımcı Profili"] = pdf_data.get("Yatırımcı Profili", "")
        
    #find tefas json for this fund and add last 7 days of price data
    tefas_json_path = os.path.join("funds_tefas_json", f"{fund['code']}.json")
    if os.path.exists(tefas_json_path) and os.path.getsize(tefas_json_path) > 0:
        with open(tefas_json_path, "r", encoding="utf-8") as f:
            tefas_data = json.load(f)
            price_history = tefas_data
            fund["Price History"] = price_history
            
    # check weather this fund is recommended in reports and add that info
    reports_folder = "reports_pdf_markdown"
    recommended = False
    for report_file in os.listdir(reports_folder):
        if report_file.endswith(".md"):
            with open(os.path.join(reports_folder, report_file), "r", encoding="utf-8") as f:
                report_content = f.read()
                if fund["code"] in report_content or fund["alias_tr"] in report_content:
                    recommended = True
                    recomendationdate = report_file.replace(".md", "")
                    fund["Recommended"] = True
                    fund["Recommendation Date"] = recomendationdate
                    break
    if not recommended:
        fund["Recommended"] = False
    enriched_fund_list.append(fund)

with open("fund_list_enriched.json", "w", encoding="utf-8") as f:
    json.dump(enriched_fund_list, f, ensure_ascii=False, indent=2)
