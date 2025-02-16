import os
import re
import time
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Constants
THREAD_COUNT = 5
MAX_RETRIES = 3
TIMEOUT = 60  # in seconds
LAST_N_YEARS = 5
BASE_URL = "https://papers.nips.cc"
OUTPUT_DIR = "D:/scraped-pdfs/"

def main():
    executor = ThreadPoolExecutor(max_workers=THREAD_COUNT)
    current_year = datetime.now().year

    try:
        print(f"Connecting to main page: {BASE_URL}")
        response = requests.get(BASE_URL, timeout=TIMEOUT)
        response.raise_for_status()  # Raise an error if request fails
        print("Successfully connected to main page.")

        soup = BeautifulSoup(response.text, "html.parser")
        year_links = soup.select("a[href^='/paper_files/paper/']")

        for year_link in year_links:
            href = year_link["href"]
            year = extract_year(href)
            if year == -1 or year < (current_year - LAST_N_YEARS) or year > current_year:
                continue

            year_url = BASE_URL + href
            print(f"Checking URL: {year_url}")

            year_folder = os.path.join(OUTPUT_DIR, str(year))
            os.makedirs(year_folder, exist_ok=True)
            print(f"Processing year: {year_url}")

            try:
                time.sleep(2)  # Delay between requests
                year_response = requests.get(year_url, timeout=TIMEOUT)
                year_response.raise_for_status()

                year_soup = BeautifulSoup(year_response.text, "html.parser")
                paper_links = year_soup.select("ul.paper-list li a[href$='Abstract-Conference.html']")
                print(f"Found {len(paper_links)} papers.")

                for paper_link in paper_links:
                    executor.submit(process_paper, BASE_URL + paper_link["href"], year_folder)
            except (requests.RequestException, Exception) as e:
                print(f"Error processing year {year}: {e}")

    except requests.RequestException as e:
        print(f"Error connecting to main page: {e}")

    executor.shutdown()

def extract_year(href):
    """Extracts the year from the given URL."""
    match = re.search(r"\d{4}", href)
    return int(match.group()) if match else -1

def process_paper(paper_url, year_folder):
    """Processes individual paper pages to find and download PDFs."""
    for attempt in range(MAX_RETRIES):
        try:
            print(f"Processing paper: {paper_url}")
            time.sleep(2)  # Delay between requests
            response = requests.get(paper_url, timeout=TIMEOUT)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            pdf_link = soup.select_one("a[href$='Paper-Conference.pdf']")
            if pdf_link:
                pdf_url = BASE_URL + pdf_link["href"]
                print(f"Downloading PDF: {pdf_url}")
                download_pdf(pdf_url, year_folder, sanitize_filename(soup.title.string))
            else:
                print(f"No PDF found for: {paper_url}")
            return
        except (requests.RequestException, Exception) as e:
            print(f"Retry {attempt + 1} for: {paper_url} - Error: {e}")
            if attempt == MAX_RETRIES - 1:
                print(f"Failed: {paper_url}")

def download_pdf(pdf_url, year_folder, file_name):
    """Downloads the PDF file and saves it locally."""
    try:
        response = requests.get(pdf_url, stream=True, timeout=TIMEOUT)
        response.raise_for_status()
        os.makedirs(year_folder, exist_ok=True)

        file_path = os.path.join(year_folder, f"{file_name}.pdf")
        with open(file_path, "wb") as pdf_file:
            for chunk in response.iter_content(8192):
                pdf_file.write(chunk)
        
        print(f"Saved PDF: {file_path}")
    except requests.RequestException as e:
        print(f"Error downloading {pdf_url}: {e}")

def sanitize_filename(filename):
    """Sanitizes the filename to remove invalid characters."""
    return re.sub(r'[\\/:*?"<>|]', "_", filename)

if __name__ == "__main__":
    main()
