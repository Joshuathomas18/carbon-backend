import pymupdf4llm
import os
import glob

# Find all PDFs in the current folder
pdf_files = glob.glob("*.pdf")

for pdf in pdf_files:
    print(f"Converting {pdf} to Markdown...")
    try:
        md_text = pymupdf4llm.to_markdown(pdf)
        
        # Save with the same name, but .md extension
        md_filename = pdf.replace(".pdf", ".md")
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(md_text)
    except Exception as e:
        print(f"Error converting {pdf}: {e}")

print("🔥 All PDFs successfully converted to Markdown!")
