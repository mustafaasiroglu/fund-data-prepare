import os
import glob
import requests

html_folder = "funds_html"
output_folder = "funds_pdf"
os.makedirs(output_folder, exist_ok=True)

html_files = glob.glob(os.path.join(html_folder, "*.html"))
print(f"{len(html_files)} HTML files found in {html_folder}")

for html_file in html_files:
    alias = os.path.splitext(os.path.basename(html_file))[0]

    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract PDF URL from the HTML content find <p>Fon Broşürü</p> and get the href of the parent <a> tag
    pdf_url = None
    if "<p>Fon Broşürü</p>" in html:
        start_index = html.index("<p>Fon Broşürü</p>")
        a_tag_start = html.rfind("<a ", 0, start_index)
        a_tag_end = html.find(">", a_tag_start)
        a_tag = html[a_tag_start:a_tag_end]
        href_index = a_tag.find("href=")
        if href_index != -1:
            href_start = href_index + len("href=") + 1
            href_end = a_tag.find('"', href_start)
            pdf_url = a_tag[href_start:href_end]

    if not pdf_url:
        print(f"No PDF URL found for {alias}, skipping")
        continue

    try:
        response = requests.get(f"https://www.garantibbvaportfoy.com.tr{pdf_url}")
        response.raise_for_status()

        with open(os.path.join(output_folder, f"{alias}.pdf"), "wb") as f:
            f.write(response.content)
        print(f"Downloaded PDF for {alias}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download PDF for {alias}: {e}")
