import os
import re
import requests
import json
import time

llm_endpoint = "https://mstf-openai-sw.openai.azure.com/"
llm_model = "gpt-5.2-chat"
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
        "Fon Adı": "Example Fund",
        "Fon Kodu": "EXAMPLE",
        "Fonun Eşik Değeri": "1000 TL",
        "Fonun Karşılaştırma Ölçütü": "BIST 100",
        "Fonun Halka Arz Tarihi": "01.01.2020",
        "Vergilendirme": "%15",
        "Alım Satım Esasları": "Günlük",
        "Yıllık Fon Yönetim Ücreti": "%1",
        "Yatırım Stratejisi": "Hisse senedi ağırlıklı",
        "Yatırımcı Profili": "Orta riskli yatırımcı"
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
    content = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    
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

for fund in fund_list:
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