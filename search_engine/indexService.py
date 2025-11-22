import re
import json
import asyncio
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


class IndexContent(BaseModel):
    book_id: str
    frequency: int


class indexService:
    def __init__(self, storage_path="../books_data"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)
        self.indexing_dict: Dict[str, List[Dict]] = {}

        # to keep the server's status
        self.indexing_status = {
            'is_indexing': False,
            'progress': 0,
            'total_books': 0,
            'indexed_books': 0,
            'status': 'idle',
            'start_time': None,
            'end_time': None
        }

    def tokenize(self, text: str) -> List[str]:
        """Extract words from text"""
        return re.findall(r'\b[a-z0-9]+\b', text.lower())

    @staticmethod
    def _build_partial_index(books_chunk):
        """Static method that can be pickled for multiprocessing"""
        partial_index = defaultdict(list)
        for book in books_chunk:
            # Tokenize title
            words = re.findall(r'\b[a-z0-9]+\b', book.title.lower())
            word_freq = defaultdict(int)
            for w in words:
                word_freq[w] += 1
            for word, freq in word_freq.items():
                partial_index[word].append({'book_id': book.id, 'frequency': freq})
        return dict(partial_index), len(books_chunk)

    async def build_index_parallel(self, books: List[Book], num_processes=4):
        """Build index using ProcessPoolExecutor without blocking FastAPI"""
        self.indexing_status['is_indexing'] = True
        self.indexing_status['status'] = 'indexing'
        self.indexing_status['total_books'] = len(books)
        self.indexing_status['indexed_books'] = 0
        self.indexing_status['start_time'] = datetime.now().isoformat()
        self.indexing_status['progress'] = 0

        self.indexing_dict = {}

        # Split books into chunks
        chunk_size = max(1, (len(books) + num_processes - 1) // num_processes)
        chunks = [books[i:i + chunk_size] for i in range(0, len(books), chunk_size)]

        # Get event loop
        loop = asyncio.get_running_loop()

        # Process chunks in parallel using ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=num_processes) as executor:
            # Submit all tasks
            futures = [
                loop.run_in_executor(executor, self._build_partial_index, chunk)
                for chunk in chunks
            ]

            # Process results as they complete
            for coro in asyncio.as_completed(futures):
                partial_index, processed_count = await coro

                # Merge partial index
                for word, entries in partial_index.items():
                    if word not in self.indexing_dict:
                        self.indexing_dict[word] = []
                    self.indexing_dict[word].extend(entries)

                # Update progress
                self.indexing_status['indexed_books'] += processed_count
                self.indexing_status['progress'] = int(
                    self.indexing_status['indexed_books'] / len(books) * 100
                )

        self.indexing_status['is_indexing'] = False
        self.indexing_status['status'] = 'completed'
        self.indexing_status['end_time'] = datetime.now().isoformat()
        self.indexing_status['progress'] = 100

        # Save asynchronously
        await self.save_index()

    async def save_index(self):
        """Save index to JSON files asynchronously"""
        loop = asyncio.get_running_loop()

        def _save():
            # Save inverted index
            index_file = self.storage_path / 'indexTable.json'
            with open(index_file, 'w') as f:
                json.dump(self.indexing_dict, f)

            # Save status
            status_file = self.storage_path / 'index_status.json'
            with open(status_file, 'w') as f:
                json.dump(self.indexing_status, f, indent=2)

        await loop.run_in_executor(None, _save)
