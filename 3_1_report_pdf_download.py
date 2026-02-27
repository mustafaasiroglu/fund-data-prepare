import json
import os
import requests

output_folder = "reports_pdf"
os.makedirs(output_folder, exist_ok=True)

reports_page = f"https://www.garantibbvaportfoy.com.tr/fon-onerileri"
html = requests.get(reports_page).text

# find <a href="/assets/fon-oeneri-raporu-230226-.pdf"

pdf_urls = []
start_index = 0
while True:
    start_index = html.find('<a href="/assets/fon-oeneri-raporu-', start_index)
    if start_index == -1:
        break
    end_index = html.find('.pdf"', start_index)
    if end_index == -1:
        break
    pdf_url = html[start_index + 9:end_index + 4]
    pdf_urls.append(pdf_url)
    start_index = end_index + 4
print(f"{len(pdf_urls)} PDF URLs found")

pdf_urls_filtered = []
for url in pdf_urls:
    url_digits = ''.join(filter(str.isdigit, url))

    if len(url_digits) == 6 and url_digits.endswith("26"):
        pdf_urls_filtered.append({ "id": url_digits, "url": url })

for pdf_url in pdf_urls_filtered:
    try:
        response = requests.get(f"https://www.garantibbvaportfoy.com.tr{pdf_url['url']}")
        response.raise_for_status()

        pdf_name = os.path.basename(pdf_url['id'])+".pdf"
        with open(os.path.join(output_folder, pdf_name), "wb") as f:
            f.write(response.content)
        print(f"Downloaded {pdf_name}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {pdf_url}: {e}")
    
