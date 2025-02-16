import os
import re
import PyPDF2
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

# Constants
OUTPUT_DIR = "D:/scraped-pdfs/"
OUTPUT_FILE = "extracted_data.xlsx"  # or "extracted_data.csv"

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file."""
    with open(pdf_path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text

def extract_title_and_abstract(text):
    """Extracts title and abstract from the text."""
    # Assuming the title is the first line and abstract follows
    lines = text.split('\n')
    title = lines[0].strip() if lines else ""
    abstract = ""
    for line in lines[1:]:
        if line.strip():
            abstract += line.strip() + " "
        else:
            break
    return title, abstract.strip()

def process_pdf(pdf_path):
    """Processes a single PDF file to extract title and abstract."""
    try:
        text = extract_text_from_pdf(pdf_path)
        title, abstract = extract_title_and_abstract(text)
        year = os.path.basename(os.path.dirname(pdf_path))
        return {
            "year": year,
            "title": title,
            "abstract": abstract,
            "file_path": pdf_path
        }
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return None

def main():
    # Collect all PDF paths
    pdf_paths = []
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(".pdf"):
                pdf_paths.append(os.path.join(root, file))

    # Use ThreadPoolExecutor to process PDFs in parallel
    data = []
    with ThreadPoolExecutor() as executor:
        results = executor.map(process_pdf, pdf_paths)
        for result in results:
            if result:
                data.append(result)

    # Create a DataFrame and save to Excel/CSV
    df = pd.DataFrame(data)
    df.to_excel(OUTPUT_FILE, index=False)  # or df.to_csv(OUTPUT_FILE, index=False)
    print(f"Data saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()