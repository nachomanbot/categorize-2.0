import pandas as pd
import re
import streamlit as st
import os

# Set the title of the Streamlit app
st.title("Dynamic URL Categorizer")

# Step 1: Upload Files
st.header("Upload Your Files")
uploaded_file = st.file_uploader("Upload URLs CSV", type="csv")

# Load rules.csv from the backend
rules_path = 'rules.csv'  # Path to the rules CSV on the backend
us_cities_path = 'us_cities.csv'  # Path to the US cities CSV on the backend

if os.path.exists(rules_path):
    rules_df = pd.read_csv(rules_path, encoding="ISO-8859-1")
else:
    st.error("Rules file not found on the backend.")
    st.stop()

if os.path.exists(us_cities_path):
    us_cities_df = pd.read_csv(us_cities_path, encoding="ISO-8859-1")
    city_names = us_cities_df['CITY'].str.lower().str.strip().tolist()
else:
    st.error("US cities file not found on the backend.")
    st.stop()

# Define the categorization function using dynamic rules
def categorize_url(url, title, meta_description, h1, rules_df, city_names):
    url = url.lower().strip()
    title = title.lower() if pd.notna(title) else ""
    meta_description = meta_description.lower() if pd.notna(meta_description) else ""
    h1 = h1.lower() if pd.notna(h1) else ""

    # 1. Homepage Detection (Relative and Absolute URLs)
    if re.fullmatch(r"https?://(www\.)?[^/]+(/)?(index\.html)?", url) or url in ["/", "", "index.html"]:
        return "CMS Pages"

    # Apply CSV rules (sorted by priority if applicable)
    applicable_rules = rules_df.sort_values(by='Priority') if 'Priority' in rules_df.columns else rules_df
    for _, rule in applicable_rules.iterrows():
        keyword_normalized = rule['Keyword'].lower().strip()
        location = rule['Location'].lower().strip()
        
        if location == 'url' and re.search(keyword_normalized, url):
            return rule['Category']
        elif location == 'title' and re.search(keyword_normalized, title):
            return rule['Category']
        elif location == 'meta description' and re.search(keyword_normalized, meta_description):
            return rule['Category']
        elif location == 'h1' and re.search(keyword_normalized, h1):
            return rule['Category']

    # 2. Neighborhood Pages (Detect City Names)
    if (
        any(city in url for city in city_names) and
        not any(re.search(rule['Keyword'].lower().strip(), url) for _, rule in applicable_rules.iterrows())
    ):
        return "Neighborhood Pages"

    # 3. Fallback to CMS Pages if uncategorized
    return "CMS Pages"

# Main function to process the uploaded file
def main():
    st.write("Upload a CSV file with the following columns: 'Address', 'Title 1', 'Meta Description 1', 'H1-1' for categorization.")

    # File uploader
    if uploaded_file is not None:
        try:
            # Attempt to read the CSV file with various encodings to be flexible
            encodings = ["utf-8", "ISO-8859-1", "utf-16", "cp1252"]
            for encoding in encodings:
                try:
                    df = pd.read_csv(uploaded_file, encoding=encoding, errors='replace')
                    break
                except UnicodeDecodeError:
                    continue
            else:
                st.error("Error reading CSV file. Please ensure it is saved in a compatible encoding (e.g., UTF-8, ISO-8859-1).")
                return
        
        required_columns = ["Address", "Title 1", "Meta Description 1", "H1-1"]
        if not all(column in df.columns for column in required_columns):
            st.error("The uploaded file must have the following columns: 'Address', 'Title 1', 'Meta Description 1', 'H1-1'.")
            return

        # Categorize URLs
        df["Category"] = df.apply(lambda row: categorize_url(row["Address"], row["Title 1"], row["Meta Description 1"], row["H1-1"], rules_df, city_names), axis=1)

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

# Run the app
if __name__ == "__main__":
    main()
