import json
import os
import re
import requests

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "fund_list.json")

output_folder = "funds_html"

with open("fund_list.json", "r", encoding="utf-8") as f:
    fund_list = json.load(f)

for fund in fund_list:  
    alias = fund.get("alias_tr")

    #check if html already exists for this fund
    if os.path.exists(f"{output_folder}/{alias}.html"):
        with open(f"{output_folder}/{alias}.html", "r", encoding="utf-8") as f:
            html = f.read()
    else:
        fund_detail_page = f"https://www.garantibbvaportfoy.com.tr/{alias}"
        html = requests.get(fund_detail_page).text

    with open(f"{output_folder}/{alias}.html", "w", encoding="utf-8") as f:
        f.write(html)

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

    fund["pdf_url"] = "https://www.garantibbvaportfoy.com.tr" + pdf_url if pdf_url else None

    # compare measure: find the compare-measure div inside #fund-detail section
    compare_measure = None
    fund_detail_start = html.find('Fund Measure Area Start')
    if fund_detail_start == -1:
        fund_detail_start = 0
    cm_index = html.find('id="compare-measure"', fund_detail_start)
    if cm_index != -1:
        div_start = html.index("<div", cm_index)
        div_end = html.index("</div>", div_start)
        div_content = html[div_start:div_end]
        p_match = re.search(r'<p[^>]*>(.*?)</p>', div_content, re.DOTALL)
        if p_match:
            compare_measure = p_match.group(1).strip()
    
    fund["compare_measure"] = compare_measure

    # Documents: parse all doc title/url pairs from <div id="documents">
    documents = []
    if 'id="documents"' in html:
        doc_start = html.index('id="documents"')
        # Find the end of the documents section (next </section> or end of file)
        doc_end = html.find('</section>', doc_start)
        doc_section = html[doc_start:doc_end] if doc_end != -1 else html[doc_start:]
        for m in re.finditer(
            r'<a[^>]*href="([^"]+)"[^>]*>\s*<p[^>]*>([^<]+)</p>',
            doc_section,
            re.DOTALL,
        ):
            href = m.group(1).strip()
            title = m.group(2).strip()
            if title and href and not href.startswith("javascript:"):
                url = "https://www.garantibbvaportfoy.com.tr" + href
                documents.append({"title": title, "url": url})
    fund["documents"] = documents


with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(fund_list, f, ensure_ascii=False, indent=2) 

    
