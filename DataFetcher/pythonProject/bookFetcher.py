import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

urls = [
    "https://www.gutenberg.org/ebooks/bookshelf/654", # American
    "https://www.gutenberg.org/ebooks/bookshelf/653" # British
]
base_url = "https://www.gutenberg.org"
books_per_main_url = 1000

session = requests.Session()  # keeps connection alive (faster)
books_to_download = []
for main_url in urls:
    current_url = main_url
    page_counter = 0
    books_for_this_url = 0
    while current_url and books_for_this_url < books_per_main_url:
        resp = session.get(current_url)
        soup = BeautifulSoup(resp.content, "html.parser")
        page_counter += 1

        # get book entries
        for item in soup.select("li.booklink a"):
            books_to_download.append(base_url + item["href"])
            books_for_this_url += 1

        # next page
        next_tag = soup.find("a", title="Go to the next page of results.")
        current_url = base_url + next_tag["href"] if next_tag else None
        print(f"Processed page {page_counter}: {current_url}")

    print("Collected:", len(books_to_download), "books")

    os.makedirs("books", exist_ok=True)

print("books to download:", len(books_to_download))



def sanitize_filename(title):
    # replace illegal Windows characters with safe alternatives
    replacements = {
        '?': '_',
        ':': '-',
        '"': "'",
        '/': '-',
        '\\': '-',
        '*': '_',
        '<': '(',
        '>': ')',
        '|': '_'
    }
    for char, repl in replacements.items():
        title = title.replace(char, repl)
    return title

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

        filename = sanitize_filename(f"{title} - {author}") + ".txt"
        with open("books/" + filename, "wb") as f:
            f.write(data)

        return "✅ Downloaded: " + filename
    except Exception as e:
        return f"❌ Error with {book_page_url}: {e}"

# use 10 threads (fast without being banned from the website)
with ThreadPoolExecutor(max_workers=10) as ex:
    for result in ex.map(download_book, books_to_download):
        print(result)
