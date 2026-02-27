from markitdown import MarkItDown
import os

output_folder = "reports_pdf_markdown"
os.makedirs(output_folder, exist_ok=True)

# Initialize MarkItDown
md = MarkItDown()
# Convert PDF files to Markdown
pdf_folder = "reports_pdf"

for pdf_file in os.listdir(pdf_folder):
    if pdf_file.endswith(".pdf"):
        pdf_path = os.path.join(pdf_folder, pdf_file)
        result = md.convert(pdf_path)
        markdown_content = result.text_content

        # Save the Markdown content to a .md file
        md_file_name = os.path.splitext(pdf_file)[0] + ".md"
        md_file_path = os.path.join(output_folder, md_file_name)

        with open(md_file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Converted {pdf_file} to {md_file_name}")