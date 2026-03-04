import os
import re
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()

llm_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
llm_model = os.getenv("AZURE_OPENAI_DEPLOYMENT")  
llm_api_key = os.getenv("AZURE_OPENAI_KEY")

output_folder = "funds_pdf_json"
os.makedirs(output_folder, exist_ok=True)

def extract_fund_data_from_md(alias):
    md_file_path = f"funds_pdf_markdown/{alias}.md"
    with open(md_file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    # Use LLM to extract data from md_content
    # This is a placeholder for the actual LLM extraction logic
    sample_data = {
        "investor_profile": "Yatırımcı Profili",
        "investment_strategy": "Yatırım Stratejisi",
        "taxation": "Vergilendirme",
        "trading_terms": "Alım Satım Esasları",
        "compare_measure": "Fonun Eşik Değeri eg.  %100 BIST-KYD1 Aylık Mevduat TL Endeksi",
        "offering_date": "Fonun Halka Arz Tarihi",
        "annual_fee": "Yıllık Fon Yönetim Ücreti"
    }

    prompt = f"""Extract the following information from the given markdown content about a fund. Return ONLY a valid JSON object, no markdown formatting, no code blocks, no extra text: """ + json.dumps(sample_data, ensure_ascii=False, indent=2)

    url = f"{llm_endpoint}openai/deployments/{llm_model}/chat/completions?api-version=2024-06-01"
    headers = {
        "Content-Type": "application/json",
        "api-key": llm_api_key
    }

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": md_content}
    ]
    
    response = requests.post(url, headers=headers, json={"messages": messages, "response_format": {"type": "json_object"}})
    resp_json = response.json()
    if response.status_code != 200 or "error" in resp_json:
        print(f"API error for {alias}: {response.status_code} - {resp_json.get('error', resp_json)}")
        return None
    content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    # Strip markdown code block formatting if present
    content = content.strip()
    content = re.sub(r'^```(?:json)?\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    content = content.strip()
    
    try:
        extracted_data = json.loads(content)
    except json.JSONDecodeError:
        print(f"Failed to parse LLM response as JSON: {content[:200]}")
        return None
    return extracted_data

fund_list_path = "fund_list.json"
with open(fund_list_path, "r", encoding="utf-8") as f:
    fund_list = json.load(f)

for fund in fund_list:  # Process only the first 4 funds for testing
    alias = fund["alias_tr"]
    if not alias:
        continue
    details = extract_fund_data_from_md(alias)
    if not details:
        print(f"No details extracted for {alias}, skipping")
        continue
    output_path = os.path.join(output_folder, f"{fund['code']}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=4)
    print(f"Extracted data for {alias} and saved to {output_path}")
    time.sleep(1)  # Be respectful to the API and avoid overwhelming it