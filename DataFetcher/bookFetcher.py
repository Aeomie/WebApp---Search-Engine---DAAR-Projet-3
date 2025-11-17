import os
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

urls = [
    "https://www.gutenberg.org/ebooks/bookshelf/654",  # American
    "https://www.gutenberg.org/ebooks/bookshelf/653"  # British
]
base_url = "https://www.gutenberg.org"
books_per_main_url = 1000

session = requests.Session()
books_to_download = []
BOOKS_SAVE_LOCATION = "../books/"
JSON_CATALOG_FILE = "../books_catalog.json"

# Dictionary to store book catalog
books_catalog = {}


def save_to_json(catalog, output_file=JSON_CATALOG_FILE):
    """
    Save the books catalog to a JSON file.

    Args:
        catalog (dict): Dictionary of books with their metadata
        output_file (str): Path to output JSON file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)

        print(f"\n{'=' * 60}")
        print(f"✅ Successfully saved catalog to: {output_file}")
        print(f"{'=' * 60}")
        print(f"Summary:")
        print(f"  Total books: {len(catalog)}")
        print(f"  Files location: ./books/")
        print(f"  Catalog file: {output_file}")
        print(f"{'=' * 60}\n")

        return True

    except Exception as e:
        print(f"\n❌ Error saving catalog: {e}")
        return False


def download_book(book_page_url):
    """
    Download a single book from Gutenberg and add it to the catalog.

    Args:
        book_page_url (str): URL of the book's page on Gutenberg

    Returns:
        str: Status message
    """
    try:
        # Extract Gutenberg ID from URL
        gutenberg_id = int(book_page_url.split("/")[-1])

        r = session.get(book_page_url)
        soup = BeautifulSoup(r.content, "html.parser")

        # Find plain text link
        link = soup.find("a", href=lambda h: h and h.endswith(".txt.utf-8"))
        if not link:
            return f"❌ No text link: {book_page_url}"

        file_url = base_url + link["href"]

        # Download text
        data = session.get(file_url).content

        # Extract title and author
        title = soup.find("h1").text.strip() if soup.find("h1") else f"Book {gutenberg_id}"
        author = soup.find("h2").text.strip() if soup.find("h2") else "Unknown"

        # Save with Gutenberg ID as filename
        filename = f"{gutenberg_id}.txt"
        file_path = os.path.join(BOOKS_SAVE_LOCATION, filename)

        with open(file_path, "wb") as f:
            f.write(data)

        # Add to catalog
        books_catalog[gutenberg_id] = {
            "id": gutenberg_id,
            "title": title,
            "author": author,
            "file_path": file_path,
            "source_url": book_page_url
        }

        return f"✅ Downloaded: {gutenberg_id} - {title}"

    except Exception as e:
        return f"❌ Error with {book_page_url}: {e}"


# Main execution
if __name__ == "__main__":
    # Collect book URLs
    for main_url in urls:
        current_url = main_url
        page_counter = 0
        books_for_this_url = 0

        while current_url and books_for_this_url < books_per_main_url:
            resp = session.get(current_url)
            soup = BeautifulSoup(resp.content, "html.parser")
            page_counter += 1

            for item in soup.select("li.booklink a"):
                books_to_download.append(base_url + item["href"])
                books_for_this_url += 1

            next_tag = soup.find("a", title="Go to the next page of results.")
            current_url = base_url + next_tag["href"] if next_tag else None
            print(f"Processed page {page_counter}: {current_url}")

        print(f"Collected {books_for_this_url} books from {main_url}")

    os.makedirs(BOOKS_SAVE_LOCATION, exist_ok=True)
    print(f"\nTotal books to download: {len(books_to_download)}\n")

    # Download books with threading
    with ThreadPoolExecutor(max_workers=10) as ex:
        for result in ex.map(download_book, books_to_download):
            print(result)

    # Save catalog to JSON
    save_to_json(books_catalog)