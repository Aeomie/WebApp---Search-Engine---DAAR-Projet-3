import re
import json
import asyncio
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel


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

    def build_index(self, book):
        self.indexing_status['is_indexing'] = True
        self.indexing_status['status'] = 'indexing'
        self.indexing_status['total_books'] = len(books)
        self.indexing_status['indexed_books'] = 0
        self.indexing_status['start_time'] = datetime.now().isoformat()
        self.indexing_status['end_time'] = None

        self.indexing_dict = {}

        books_list_size = len(books)
        for i, book in enumerate(books):
            # Tokenize
            words = self.tokenize(book.title)

            # Count word frequencies
            word_freq = defaultdict(int)
            for word in words:
                word_freq[word] += 1

            for word, freq in word_freq.items():
                if word not in self.indexing_dict:
                    self.indexing_dict[word] = []

                self.indexing_dict[word].append({
                    'book_id': book.id,
                    'frequency': freq
                })

            self.indexing_status['indexed_books'] = i + 1
            self.indexing_status['progress'] = int((i + 1) / books_list_size * 100)
            # Yield control to allow other requests (every 10 books) incase the user wants to check on status

        # Saving the content
        self.save_index()
        self.indexing_status['is_indexing'] = False
        self.indexing_status['status'] = 'completed'
        self.indexing_status['end_time'] = datetime.now().isoformat()

        return {
            'success': True,
            'total_books': books_list_size,
        }

    def save_index(self):
        """Save index to JSON files (async)"""
        # Save inverted index
        index_file = self.storage_path / 'indexTable.json'
        with open(index_file, 'w') as f:
            json.dump(self.indexing_dict, f)

        # Optionally save status separately
        status_file = self.storage_path / 'index_status.json'
        with open(status_file, 'w') as f:
            json.dump(self.indexing_status, f, indent=2)
