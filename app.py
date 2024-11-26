import pandas as pd
import re
import streamlit as st
import os
import csv

# Set the title of the Streamlit app
st.title("Dynamic URL Categorizer with Similarity Matching")

# Step 1: Upload Files
st.header("Upload Your Files")
uploaded_file = st.file_uploader("Upload URLs CSV for Categorization", type="csv")

# Load reference CSV with pre-categorized entries
reference_path = os.path.join(os.path.dirname(__file__), 'reference_urls.csv')  # Path to the reference CSV on the backend
if os.path.exists(reference_path):
    reference_df = pd.read_csv(reference_path, encoding="ISO-8859-1")
    required_reference_columns = ["Address", "Title", "Meta Description"]
    # Handle missing columns gracefully
    existing_columns = [col for col in required_reference_columns if col in reference_df.columns]
    if existing_columns:
        reference_df['combined_text'] = reference_df[existing_columns].fillna('').apply(lambda x: ' '.join(x.astype(str)), axis=1)
    else:
        st.error("The reference file must contain at least one of the following columns: 'Address', 'Title', 'Meta Description'.")
        st.stop()
    

# Load us_cities.csv from the backend
us_cities_path = 'us_cities.csv'  # Path to the US cities CSV on the backend
if os.path.exists(us_cities_path):
    us_cities_df = pd.read_csv(us_cities_path, encoding="ISO-8859-1")
    city_names = us_cities_df['CITY'].str.lower().str.strip().tolist()
else:
    st.error("US cities file not found on the backend.")
    st.stop()

# Define the categorization function using rules from rules.csv

def load_rules():
    rules_path = 'rules.csv'
    if os.path.exists(rules_path):
        with open(rules_path, mode='r', encoding='ISO-8859-1') as file:
            reader = csv.DictReader(file)
            return list(reader)
    else:
        st.error("Rules file not found on the backend.")
        st.stop()

rules = load_rules()

def categorize_url(url, title, meta_description, h1):
    url = url.lower().strip()
    title = title.lower() if pd.notna(title) else ""
    meta_description = meta_description.lower() if pd.notna(meta_description) else ""
    h1 = h1.lower() if pd.notna(h1) else ""

    # Apply rules from rules.csv
    for rule in rules:
        keyword = rule['Keyword'].lower()
        category = rule['Category']
        location = rule['Location'].lower()
        priority = int(rule['Priority'])

        if location == 'url' and re.search(keyword, url):
            return category
        elif location == 'title' and keyword in title:
            return category
        elif location == 'meta description' and keyword in meta_description:
            return category
        elif location == 'h1' and keyword in h1:
            return category

    # Default Category if no rules matched
    return "CMS Pages"

# Main function to process the uploaded file
def main():
    st.write("Upload a CSV file with the following columns: 'Address', 'Title 1', 'Meta Description 1', 'H1-1' for categorization.")

    
    
    # File uploader
    if uploaded_file is not None:
        st.info("Processing the uploaded file. Please wait...")
        try:
            # Attempt to read the CSV file with various encodings to be flexible
            encodings = ["utf-8", "ISO-8859-1", "utf-16", "cp1252"]
            df = None
            for encoding in encodings:
                try:
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            if df is None:
                st.error("Error reading CSV file. Please ensure it is saved in a compatible encoding (e.g., UTF-8, ISO-8859-1).")
                return

            required_columns = ["Address", "Title 1", "Meta Description 1", "H1-1"]
            if not all(column in df.columns for column in required_columns):
                st.error("The uploaded file must have the following columns: 'Address', 'Title 1', 'Meta Description 1', 'H1-1'.")
                return

            # Categorize URLs using similarity matching
            progress_bar = st.progress(0)
            total_rows = len(df)
            
            def categorize_with_progress(row, idx):
                category = categorize_url(row["Address"], row["Title 1"], row["Meta Description 1"], row["H1-1"])
                progress_bar.progress((idx + 1) / total_rows)
                return category
            
            df["Category"] = [categorize_with_progress(row, idx) for idx, row in df.iterrows()]

            # Create output DataFrame with only Address and Category columns
            output_df = df[["Address", "Category"]]

            # Show results and allow download
            st.write("Categorized URLs:", output_df)
            st.download_button(
                label="Download Categorized CSV",
                data=output_df.to_csv(index=False),
                file_name="categorized_urls.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

# Run the app
if __name__ == "__main__":
    main()
