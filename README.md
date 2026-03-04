# Fund Data Prepare

This project collects, processes, and enriches fund data from **Garanti BBVA Portföy** to produce a single enriched fund list (`fund_list_enriched.json`).

## Prerequisites

- Python 3.10+
- Required packages: `requests`, `markitdown`
- Azure OpenAI API key set as the environment variable `AZURE_OPENAI_KEY` (used in step 2.3)

```bash
pip install requests markitdown
```

## Pipeline Overview

The pipeline is organized into numbered steps. Each step must be run **in order**, as later steps depend on outputs from earlier ones.

```
1.1  Fund List Extract          → fund_list_raw.json, fund_list.json
1.2  Fund Details HTML          → funds_html/*.html
2.1  Fund PDF Download          → funds_pdf/*.pdf
2.2  Fund PDF → Markdown        → funds_pdf_markdown/*.md
2.3  Fund PDF → JSON (via LLM)  → funds_pdf_json/*.json
3.1  Report PDF Download        → reports_pdf/*.pdf
3.2  Report PDF → Markdown      → reports_pdf_markdown/*.md
4.1  TEFAS Data Extract         → funds_tefas_json/*.json
5.1  Enrich Fund List           → fund_list_enriched.json
```

---

## Step-by-Step Guide

### Step 1.1 — Extract Fund List

```bash
python 1_1_fund_list_extract.py
```

Calls the Garanti BBVA Portföy API (`GetFundsByCategory`) and produces:
- **`fund_list_raw.json`** — raw API response
- **`fund_list.json`** — cleaned list with `code`, `title_tr`, `title_en`, `category_tr`, `category_en`, `alias_tr`, `alias_en` for each fund

### Step 1.2 — Download Fund Detail Pages (HTML)

```bash
python 1_2_fund_details_html.py
```

For every fund in `fund_list.json`, downloads the fund detail page from `garantibbvaportfoy.com.tr` and saves the HTML to `funds_html/<alias>.html`.

### Step 2.1 — Download Fund Brochure PDFs

```bash
python 2_1_fund_pdf_download.py
```

Parses each HTML file in `funds_html/` to locate the **Fon Broşürü** (fund brochure) PDF link, then downloads the PDF to `funds_pdf/<alias>.pdf`.

### Step 2.2 — Convert Fund PDFs to Markdown

```bash
python 2_2_fund_pdf_markdown.py
```

Uses the `markitdown` library to convert every PDF in `funds_pdf/` to Markdown, saving results to `funds_pdf_markdown/<alias>.md`.

### Step 2.3 — Extract Structured Data from Fund Markdown (LLM)

```bash
python 2_3_fund_pdf_json.py
```

Sends each Markdown file to **Azure OpenAI** to extract structured fund details as JSON. Extracted fields include:

| Field | Description |
|---|---|
| Fon Adı | Fund name |
| Fon Kodu | Fund code |
| Fonun Eşik Değeri | Fund threshold value |
| Fonun Karşılaştırma Ölçütü | Benchmark |
| Fonun Halka Arz Tarihi | IPO date |
| Vergilendirme | Tax information |
| Alım Satım Esasları | Trading rules |
| Yıllık Fon Yönetim Ücreti | Annual management fee |
| Yatırım Stratejisi | Investment strategy |
| Yatırımcı Profili | Investor profile |

Results are saved to `funds_pdf_json/<CODE>.json`.

> **Requires** the `AZURE_OPENAI_KEY` environment variable.

### Step 3.1 — Download Fund Recommendation Reports

```bash
python 3_1_report_pdf_download.py
```

Scrapes the **Fon Önerileri** page on `garantibbvaportfoy.com.tr` for fund recommendation report PDFs and downloads them to `reports_pdf/<date_id>.pdf`.

### Step 3.2 — Convert Report PDFs to Markdown

```bash
python 3_2_report_pdf_markdown.py
```

Converts every PDF in `reports_pdf/` to Markdown using `markitdown`, saving to `reports_pdf_markdown/<date_id>.md`.

### Step 4.1 — Extract TEFAS Historical Data

```bash
python "4_1_tefas_extract copy.py"
```

For each fund in `fund_list.json`, fetches the last 30 days of historical data from the **TEFAS** API (`tefas.gov.tr`). The following fields are collected per day:

| Field | Description |
|---|---|
| TARIH | Date |
| FIYAT | Price |
| TEDPAYSAYISI | Number of shares in circulation |
| KISISAYISI | Number of investors |
| PORTFOYBUYUKLUK | Portfolio size |

Results are saved to `funds_tefas_json/<CODE>.json`. Already-downloaded funds are skipped.

### Step 5.1 — Enrich Fund List

```bash
python 5_1_enrich_fund_list.py
```

Merges all collected data into a single enriched list:

1. Starts from `fund_list.json`
2. Adds structured brochure data from `funds_pdf_json/<CODE>.json`
3. Adds TEFAS price history from `funds_tefas_json/<CODE>.json`
4. Checks `reports_pdf_markdown/*.md` to determine if the fund appears in any recommendation report, and records the recommendation date if found

**Output:** `fund_list_enriched.json`

---

## Output Structure

Each entry in `fund_list_enriched.json` contains:

```json
{
  "code": "GAE",
  "title_tr": "...",
  "title_en": "...",
  "category_tr": "...",
  "category_en": "...",
  "alias_tr": "...",
  "alias_en": "...",
  "Fon Adı": "...",
  "Fon Kodu": "...",
  "Fonun Eşik Değeri": "...",
  "Fonun Karşılaştırma Ölçütü": "...",
  "Fonun Halka Arz Tarihi": "...",
  "Vergilendirme": "...",
  "Alım Satım Esasları": "...",
  "Yıllık Fon Yönetim Ücreti": "...",
  "Yatırım Stratejisi": "...",
  "Yatırımcı Profili": "...",
  "Price History": [ ... ],
  "Recommended": true,
}
```

## Directory Structure

| Path | Contents |
|---|---|
| `fund_list_raw.json` | Raw API response |
| `fund_list.json` | Cleaned fund list |
| `funds_html/` | Fund detail HTML pages |
| `funds_pdf/` | Fund brochure PDFs |
| `funds_pdf_markdown/` | Fund brochures as Markdown |
| `funds_pdf_json/` | Structured fund data (LLM-extracted) |
| `reports_pdf/` | Fund recommendation report PDFs |
| `reports_pdf_markdown/` | Reports as Markdown |
| `funds_tefas_json/` | TEFAS historical price data |
| `fund_list_enriched.json` | **Final enriched output** |
