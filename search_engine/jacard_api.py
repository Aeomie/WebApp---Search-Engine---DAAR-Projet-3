import re
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from concurrent.futures import ProcessPoolExecutor, as_completed


class Book(BaseModel):
    id: int
    title: str
    author: Optional[str] = None
    content: Optional[str] = None


class IndexContent(BaseModel):
    book_id: str
    frequency: int


class indexService:
    def __init__(self, storage_path="../books_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.indexing_dict: Dict[str, List[Dict]] = {}

        # Separate status for each index type
        self.indexing_status = {
            'T': {
                'is_indexing': False,
                'progress': 0,
                'total_books': 0,
                'indexed_books': 0,
                'status': 'idle',
                'start_time': None,
                'end_time': None
            },
            'TC': {
                'is_indexing': False,
                'progress': 0,
                'total_books': 0,
                'indexed_books': 0,
                'status': 'idle',
                'start_time': None,
                'end_time': None
            }
        }


    def tokenize(self, text: str) -> List[str]:
        """Extract words from text"""
        return re.findall(r'\b[a-z0-9]+\b', text.lower())

    @staticmethod
    def _build_partial_index_by_Title(books_chunk):
        """Static method that can be pickled for multiprocessing"""
        partial_index = defaultdict(list)
        for book in books_chunk:
            try:
                # Tokenize title
                words = re.findall(r'\b[a-z0-9]+\b', book.title.lower())
                word_freq = defaultdict(int)
                for w in words:
                    word_freq[w] += 1
                for word, freq in word_freq.items():
                    partial_index[word].append({'book_id': book.id, 'frequency': freq})
            except Exception as e:
                print(f"Error processing book {book.id}: {e}")
                continue
        return dict(partial_index), len(books_chunk)

    @staticmethod
    def _build_partial_index_by_Title_Content(books_chunk):
        """Static method that can be pickled for multiprocessing"""
        partial_index = defaultdict(list)
        for book in books_chunk:
            try:
                # Tokenize title + content safely
                title = book.title.lower() if book.title else ""
                content = book.content.lower() if book.content else ""
                text = title + " " + content
                words = re.findall(r'\b[a-z0-9]+\b', text)
                word_freq = defaultdict(int)
                for w in words:
                    word_freq[w] += 1
                for word, freq in word_freq.items():
                    partial_index[word].append({'book_id': book.id, 'frequency': freq})
            except Exception as e:
                print(f"Error processing book {book.id}: {e}")
                continue
        return dict(partial_index), len(books_chunk)

    @staticmethod
    def _load_books_batch(all_files: List[Path], start: int, batch_size: int) -> List[Book]:
        """Load books from file list in batches"""
        books = []
        batch_files = all_files[start:start + batch_size]

        for file in batch_files:
            try:
                with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    book_id = int(file.stem)
                    books.append(Book(id=book_id, content=content))
            except Exception as e:
                print(f"Error reading file {file}: {e}")
                continue

        return books

    def build_index_parallel(self, num_processes=4, index_type="T"):
        """Build index by streaming through catalog in batches"""
        BATCH_SIZE = 1000

        self.indexing_status[index_type]['is_indexing'] = True
        self.indexing_status[index_type]['status'] = 'indexing'
        self.indexing_status[index_type]['indexed_books'] = 0
        self.indexing_status[index_type]['start_time'] = datetime.now().isoformat()
        self.indexing_dict = {}

        # Load catalog once
        catalog_path = Path(self.storage_path) / "catalog.json"
        with open(catalog_path, 'r', encoding='utf-8', errors='ignore') as f:
            catalog = json.load(f)

        all_book_ids = list(catalog.keys())
        self.indexing_status[index_type]['total_books'] = len(all_book_ids)

        # Process in batches
        for batch_start in range(0, len(all_book_ids), BATCH_SIZE):
            batch_ids = all_book_ids[batch_start:batch_start + BATCH_SIZE]

            # Load books for this batch
            books = []
            for book_id in batch_ids:
                try:
                    book_data = catalog[book_id]
                    content = ""

                    # Read content if needed for TC index
                    if index_type == "TC":
                        file_path = Path(book_data['file_path'])
                        if file_path.exists():
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content = f.read()
                            except Exception as e:
                                print(f"Warning: Could not read {file_path}: {e}")
                                content = ""

                    books.append(Book(
                        id=int(book_id),
                        title=book_data['title'],
                        author=book_data.get('author'),
                        content=content
                    ))
                except Exception as e:
                    print(f"Error processing book_id {book_id}: {e}")
                    continue

            # Skip if no books loaded
            if len(books) == 0:
                continue

            # Process with workers
            chunk_size = max(1, len(books) // num_processes)
            chunks = [books[i:i + chunk_size] for i in range(0, len(books), chunk_size)]

            with ProcessPoolExecutor(max_workers=num_processes) as executor:
                method = self._build_partial_index_by_Title if index_type == "T" else self._build_partial_index_by_Title_Content
                futures = [executor.submit(method, chunk) for chunk in chunks]

                for future in as_completed(futures):
                    partial_index, count = future.result()
                    for word, entries in partial_index.items():
                        if word not in self.indexing_dict:
                            self.indexing_dict[word] = []
                        self.indexing_dict[word].extend(entries)

                    self.indexing_status[index_type]['indexed_books'] += count
                    self.indexing_status[index_type]['progress'] = int(
                        self.indexing_status[index_type]['indexed_books'] / len(all_book_ids) * 100
                    )

            del books
        self.indexing_status[index_type]['is_indexing'] = False
        self.indexing_status[index_type]['end_time'] = datetime.now().isoformat()
        self.indexing_status[index_type]['progress'] = 100

        self.save_index(index_type)
        self.indexing_status[index_type]['status'] = 'completed'

    def save_index(self, index_type: str):
        """Save index to JSON files"""
        # Save inverted index
        file_name = f"index_Table{index_type}.json"
        index_file = self.storage_path / file_name
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.indexing_dict, f, ensure_ascii=False)

        # Save status
        status_file_name = f"index_status_{index_type}.json"
        status_file = self.storage_path / status_file_name
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump(self.indexing_status, f, indent=2, ensure_ascii=False)