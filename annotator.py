import pandas as pd
import google.generativeai as genai
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import json
import os

# Configuration
DATA_FILE = r"D:\DATASCIENCE\extracted_data.xlsx"  # Use raw string for Windows paths
OUTPUT_FILE = r"D:\DATASCIENCE\annotated_data.csv"  # Use raw string for Windows paths
GEMINI_API_KEY = "AIzaSyCPbom6-1vcL53j3GneDBEHEIEfpsDSIxY"  # Replace with your Gemini API key

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# Define annotation categories
CATEGORIES = [
    "Deep Learning/Machine Learning",
    "Computer Vision",
    "Reinforcement Learning",
    "Natural Language Processing (NLP)",
    "Optimization Algorithms"
]

# Create output file with headers if it doesn't exist
if not os.path.exists(OUTPUT_FILE):
    pd.DataFrame(columns=['title', 'Category', 'Authors']).to_csv(OUTPUT_FILE, index=False, mode='w')

def classify_paper(title, retries=3, delay=10):
    """
    Classifies a research paper into one of the predefined categories and extracts authors using the Gemini API.
    """
    abstract = "No abstract available"  # Placeholder for abstract (not provided in the dataset)

    for attempt in range(retries):
        try:
            # Construct the prompt for classification
            prompt = f"""
            Classify the following research paper into one of these categories: {', '.join(CATEGORIES)}.
            Also, extract the authors' names based on research trends or common knowledge. If unknown, return "Unknown".

            Respond in JSON format:
            {{
                "Category": "Selected Category",
                "Authors": "Author1, Author2, ..."
            }}

            Title: "{title}"
            Abstract: "{abstract}"
            """

            # Send the prompt to the Gemini API
            response = model.generate_content(prompt)
            response_text = response.text.strip()

            # Parse the JSON response
            try:
                result = json.loads(response_text)
                category = result.get("Category", "Unknown").strip()
                authors = result.get("Authors", "Unknown").strip()

                # Validate the category
                if category not in CATEGORIES:
                    category = "Unknown"

                return category, authors

            except json.JSONDecodeError:
                print(f"Invalid JSON response for '{title}'. Retrying...")
                continue

        except Exception as e:
            if "429" in str(e) or "ResourceExhausted" in str(e):  # Handle rate limits
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                print(f"Error classifying '{title}': {e}")
                return "Error", "Error"

    print(f"Max retries reached for '{title}'. Skipping...")
    return "Error", "Error"

def process_dataset():
    """
    Processes the dataset to classify papers and extract authors using multithreading.
    """
    # Load the dataset
    try:
        df = pd.read_excel(DATA_FILE)  # Use read_excel for .xlsx files
    except FileNotFoundError:
        raise ValueError(f"Dataset file not found: {DATA_FILE}")

    # Ensure the required column exists
    if 'title' not in df.columns:
        raise ValueError("Dataset must contain a 'title' column.")

    # Initialize counters
    total_papers = len(df)
    processed_count = 0

    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(classify_paper, row['title']): index
            for index, row in df.iterrows()
        }

        for future in as_completed(futures):
            index = futures[future]
            try:
                category, authors = future.result()
                processed_count += 1
                print(f"Processed {processed_count}/{total_papers}: {category}, Authors: {authors}")

                # Append the result to the output file
                result_row = [[df.at[index, 'title'], category, authors]]
                pd.DataFrame(result_row, columns=['title', 'Category', 'Authors']).to_csv(
                    OUTPUT_FILE, index=False, mode='a', header=False
                )

            except Exception as e:
                print(f"Error processing paper {index + 1}: {e}")

    print(f"Annotation complete! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_dataset()