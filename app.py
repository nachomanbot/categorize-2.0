import pandas as pd
import re
import streamlit as st
import os
import csv

# Load US cities as a static resource
@st.cache_data
def load_us_cities():
    us_cities_path = "us_cities.csv"
    us_cities = pd.read_csv(us_cities_path)['CITY'].str.lower().tolist()
    return us_cities

# Load categorization rules from rules.csv
def load_rules():
    rules_path = 'rules.csv'
    if os.path.exists(rules_path):
        with open(rules_path, mode='r', encoding='ISO-8859-1') as file:
            reader = csv.DictReader(file)
            return list(reader)
    else:
        st.error("Rules file not found on the backend.")
        st.stop()

# Define the categorization function
def categorize_url(url, title, meta_description, h1, us_cities, rules):
    url = url.lower().strip()
    title = title.lower() if pd.notna(title) else ""
    meta_description = meta_description.lower() if pd.notna(meta_description) else ""
    h1 = h1.lower() if pd.notna(h1) else ""

    # Apply rules from rules.csv
    for rule in rules:
        keyword = rule['Keyword'].lower()
        category = rule['Category']
        location = rule['Location'].lower()

        if location == 'url' and re.search(keyword, url):
            return category
        elif location == 'title' and keyword in title:
            return category
        elif location == 'meta description' and keyword in meta_description:
            return category
        elif location == 'h1' and keyword in h1:
            return category

    # 1. Homepage Detection (Relative and Absolute URLs)
    if re.fullmatch(r"https?://(www\.)?[^/]+(/)?(index\.html)?", url) or url in ["/", "", "index.html"]:
        return "CMS Pages"

    # 2. Neighborhood Pages (Detect City Names)
    if any(city in url for city in us_cities):
        # Check for MLS keywords in title or meta description
        if any(keyword in title or keyword in meta_description for keyword in ["sell", "buy", "sale"]):
            return "MLS Pages"
        return "Neighborhood Pages"

    # Fallback to CMS Pages if uncategorized
    return "CMS Pages"

# Main function
def main():
    st.title("URL Categorizer")
    st.write("Upload a CSV file with the following columns: 'URL', 'Title 1', 'Meta Description 1', 'H1-1' for categorization.")

    # File uploader
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
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

            required_columns = ["URL", "Title 1", "Meta Description 1", "H1-1"]
            if not all(column in df.columns for column in required_columns):
                st.error("The uploaded file must have the following columns: 'URL', 'Title 1', 'Meta Description 1', 'H1-1'.")
                return

            us_cities = load_us_cities()
            rules = load_rules()

            # Categorize URLs
            df["Category"] = df.apply(lambda row: categorize_url(row["URL"], row["Title 1"], row["Meta Description 1"], row["H1-1"], us_cities, rules), axis=1)

            # Create output DataFrame with only Address and Category columns
            output_df = df[["URL", "Category"]]

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
