import pandas as pd
import re
import streamlit as st

# Load US cities as a static resource
@st.cache_data
def load_us_cities():
    us_cities_path = "us_cities.csv"
    us_cities = pd.read_csv(us_cities_path)['CITY'].str.lower().tolist()
    return us_cities

# Define the categorization function
def categorize_url(url, us_cities):
    url = url.lower()

    # 1. Blog Filters
    if re.search(r'/tag|/category', url):
        return "Blog Filters"

    # 2. Blog Pages
    if re.search(r'/blog', url) and not re.search(r'/page|/author', url):
        return "Blog Pages"

    # 3. Property Pages
    if re.search(r'/properties|/property|/homes-for-sale|/rent|/listings|/rentals', url) and not re.search(r'/page', url):
        return "Property Pages"

    # 4. Parameters
    if re.search(r'\?.+=', url):
        return "Parameters"

    # 5. Pagination
    if re.search(r'/page/\d+', url):
        return "Pagination"

    # 6. Homepage (Prioritized)
    if url.endswith("/") or re.fullmatch(r"https?://[^/]+/?", url):
        return "CMS Pages"

    # 7. Neighborhood Pages (Detect City Names)
    if (
        any(city in url for city in us_cities) and
        not re.search(r'/blog|/properties|/property|/listings|/agent|/team|/contact|/about|/testimonials|/privacy|/tos|/terms|/resources|/sell|/purchase|/films', url)
    ):
        return "Neighborhood Pages"

    # 8. Agent Pages
    if re.search(r'/agent|/team', url):
        return "Agent Pages"

    # 9. CMS Pages (Contact, Testimonials, About, etc.)
    if re.search(r'/contact|/about|/testimonials|/privacy|/tos|/terms|/resources|/sell|/purchase|/films', url):
        return "CMS Pages"

    # Fallback to CMS Pages if uncategorized
    return "CMS Pages"

# Main function
def main():
    st.title("URL Categorizer")
    st.write("Upload a CSV file with a column named 'URL' for categorization.")

    # File uploader
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        if "URL" not in df.columns:
            st.error("The uploaded file must have a column named 'URL'.")
            return

        us_cities = load_us_cities()

        # Categorize URLs
        df["Category"] = df["URL"].apply(lambda url: categorize_url(url, us_cities))

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
