import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

urls = [
    "https://www.gutenberg.org/ebooks/bookshelf/654",
    "https://www.gutenberg.org/ebooks/bookshelf/653"
]
base_url = "https://www.gutenberg.org"

session = requests.Session()  # keeps connection alive (faster)
books_to_download = []

for start_url in urls:
    current_url = start_url
    while current_url:
        resp = session.get(current_url)
        soup = BeautifulSoup(resp.content, "html.parser")

        # get book entries
        for item in soup.select("li.booklink a"):
            books_to_download.append(base_url + item["href"])

        # next page
        next_tag = soup.find("a", title="Go to the next page of results.")
        current_url = base_url + next_tag["href"] if next_tag else None

print("Collected:", len(books_to_download), "books")

os.makedirs("books", exist_ok=True)

def download_book(book_page_url):
    try:
        r = session.get(book_page_url)
        soup = BeautifulSoup(r.content, "html.parser")

        # find plain text link
        link = soup.find("a", href=lambda h: h and h.endswith(".txt.utf-8"))
        if not link:
            return "❌ No text link: " + book_page_url

        file_url = base_url + link["href"]

        # download text
        data = session.get(file_url).content

        # title from page header
        title = soup.find("h1").text.strip()
        author = soup.find("h2").text.strip() if soup.find("h2") else "Unknown"

        filename = f"{title} - {author}.txt".replace("/", "_")
        with open("books/" + filename, "wb") as f:
            f.write(data)

        return "✅ Downloaded: " + filename
    except Exception as e:
        return f"❌ Error with {book_page_url}: {e}"

# use 10 threads (fast without being banned from the website)
with ThreadPoolExecutor(max_workers=10) as ex:
    for result in ex.map(download_book, books_to_download):
        print(result)
