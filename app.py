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
def categorize_url(url, rules_df, city_names):
    url = url.lower()

    # Apply CSV rules (sorted by priority if applicable)
    applicable_rules = rules_df.sort_values(by='Priority') if 'Priority' in rules_df.columns else rules_df
    for _, rule in applicable_rules.iterrows():
        keyword_normalized = rule['Keyword'].lower().strip()
        if re.search(keyword_normalized, url):
            return rule['Category']

    # 1. Neighborhood Pages (Detect City Names)
    if (
        any(city in url for city in city_names) and
        not any(re.search(rule['Keyword'].lower().strip(), url) for _, rule in applicable_rules.iterrows())
    ):
        return "Neighborhood Pages"

    # 2. Fallback to CMS Pages if uncategorized
    return "CMS Pages"

# Main function to process the uploaded file
def main():
    st.write("Upload a CSV file with a column named 'URL' for categorization.")

    # File uploader
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "URL" not in df.columns:
            st.error("The uploaded file must have a column named 'URL'.")
            return

        # Categorize URLs
        df["Category"] = df["URL"].apply(lambda url: categorize_url(url, rules_df, city_names))

        # Show results and allow download
        st.write("Categorized URLs:", df)
        st.download_button(
            label="Download Categorized CSV",
            data=df.to_csv(index=False),
            file_name="categorized_urls.csv",
            mime="text/csv"
        )

# Run the app
if __name__ == "__main__":
    main()
