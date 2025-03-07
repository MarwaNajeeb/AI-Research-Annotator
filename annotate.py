import os
import openai
import pandas as pd

# Set up OpenAI API key
openai.api_key = "AIzaSyCPbom6-1vcL53j3GneDBEHEIEfpsDSIxY"  # Replace with your OpenAI API key

# Define the five annotation labels
ANNOTATION_LABELS = [
    "Deep Learning",
    "Computer Vision",
    "Reinforcement Learning",
    "Natural Language Processing (NLP)",
    "Optimization"
]

# Directory containing scraped papers
SCRAPED_DIR = "F:\BS Software Engineering/scraped-pdfs/"

# Output file for annotated dataset
OUTPUT_FILE = "D:\DATASCIENCE\annotate_papers.csv"

# Function to extract text from PDF files (dummy implementation)
def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file.
    Replace this with a proper PDF text extraction library like PyPDF2 or pdfminer.
    """
    try:
        # Example: Using PyPDF2 (install with `pip install PyPDF2`)
        from PyPDF2 import PdfReader
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return None

# Function to classify a paper using the LLM API
def classify_paper(title, abstract):
    """
    Sends the title and abstract to the LLM API for classification.
    """
    # Combine title and abstract for context
    prompt = f"Title: {title}\nAbstract: {abstract}\n\nClassify this research paper into one of the following categories: {', '.join(ANNOTATION_LABELS)}. Return only the category name."

    # Call the OpenAI API
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use the appropriate model
        prompt=prompt,
        max_tokens=50,
        temperature=0.5,
        stop=None
    )

    # Extract the predicted label from the API response
    predicted_label = response.choices[0].text.strip()
    return predicted_label

# Function to annotate the dataset
def annotate_dataset():
    """
    Iterates through the scraped papers, extracts text, and annotates them using the LLM API.
    """
    # Prepare a list to store annotated data
    annotated_data = []

    # Iterate through each year folder
    for year in os.listdir(SCRAPED_DIR):
        year_folder = os.path.join(SCRAPED_DIR, year)
        if not os.path.isdir(year_folder):
            continue

        # Iterate through each PDF file in the year folder
        for pdf_file in os.listdir(year_folder):
            if not pdf_file.endswith(".pdf"):
                continue

            pdf_path = os.path.join(year_folder, pdf_file)
            print(f"Processing: {pdf_path}")

            # Extract text from the PDF
            text = extract_text_from_pdf(pdf_path)
            if not text:
                continue

            # Extract title and abstract (dummy implementation)
            # Replace this with proper logic to extract title and abstract from the text
            title = pdf_file.replace(".pdf", "")  # Use filename as title
            abstract = text[:500]  # Use first 500 characters as abstract

            # Classify the paper
            try:
                label = classify_paper(title, abstract)
                print(f"Paper: {title}\nPredicted Label: {label}\n")
                annotated_data.append({
                    "title": title,
                    "abstract": abstract,
                    "year": year,
                    "annotation": label
                })
            except Exception as e:
                print(f"Error classifying paper: {title}\nError: {e}\n")
                annotated_data.append({
                    "title": title,
                    "abstract": abstract,
                    "year": year,
                    "annotation": "Unknown"
                })

    # Convert the annotated data to a DataFrame
    df = pd.DataFrame(annotated_data)

    # Save the annotated dataset to a CSV file
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Annotation complete! Annotated dataset saved to {OUTPUT_FILE}.")

# Run the annotation process
if __name__ == "__main__":
    annotate_dataset()