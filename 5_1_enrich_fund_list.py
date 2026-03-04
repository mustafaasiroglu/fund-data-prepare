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

        fund["investor_profile"] = pdf_data.get("investor_profile")
        fund["investment_strategy"] = pdf_data.get("investment_strategy")
        fund["taxation"] = pdf_data.get("taxation")
        fund["trading_terms"] = pdf_data.get("trading_terms")

        
    #find tefas json for this fund and add last 7 days of price data
    # tefas_json_path = os.path.join("funds_tefas_json", f"{fund['code']}.json")
    # if os.path.exists(tefas_json_path) and os.path.getsize(tefas_json_path) > 0:
    #     with open(tefas_json_path, "r", encoding="utf-8") as f:
    #         tefas_data = json.load(f)
    #         price_history = tefas_data
    #         fund["Price History"] = price_history
            
    # check weather this fund is recommended in reports and add that info
    reports_folder = "reports_pdf_markdown"
    recommended = False

    #find latest report file (by date in filename) 
    latest_report_file = None
    latest_report_date = None
    for report_file in os.listdir(reports_folder):
        if report_file.endswith(".md"):
            report_date_str = report_file.replace(".md", "")
            try:
                report_date = datetime.datetime.strptime(report_date_str, "%d%m%y")
                if not latest_report_date or report_date > latest_report_date:
                    latest_report_date = report_date
                    latest_report_file = report_file
            except ValueError:
                continue

    #fill recommended field
    if latest_report_file:
        with open(os.path.join(reports_folder, latest_report_file), "r", encoding="utf-8") as f:
            report_content = f.read()
            if fund["code"] in report_content or fund["alias_tr"] in report_content:  
                fund["recommended"] = True
            else:
                fund["recommended"] = False
    else:
        print("No report files found in reports_pdf_markdown folder.")
        fund["recommended"] = False

    
    enriched_fund_list.append(fund)

with open("fund_list_enriched.json", "w", encoding="utf-8") as f:
    json.dump(enriched_fund_list, f, ensure_ascii=False, indent=2)
