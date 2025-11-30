import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from pathlib import Path
from datetime import datetime
import numpy as np


class JaccardGraph:
    def __init__(self, threshold=0.1, max_frac=0.2):
        self.threshold = threshold
        self.graph: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        self.book_words: Dict[int, Set[str]] = {}
        self.inverted_index: Dict[str, List[Tuple[int, float]]] = {}
        self.pagerank_scores: Dict[int, float] = {}
        self.max_frac = max_frac
        self.graph_save_location = "../books_data/jaccard_graph.json"
        self.pagerank_score_save_location = "../books_data/pagerank_scores.json"
        self.progress = {
            "total_pairs": 0,
            "processed_pairs": 0,
            'is_building': False,
            'status': 'idle',
            'start_time': None,
            'end_time': None,
            'rank_status': 'idle',
            'is_ranking': False,
            'rank_start_time': None,
            'rank_end_time': None
        }

    # ---------------------------------------------------------
    # BUILD GRAPH
    # ---------------------------------------------------------

    def build_graph_from_inverted_index(self, inverted_index_path: str, catalog_path: str, progress_interval=0.05):
        """Build graph using inverted index (FAST)."""

        # Load inverted index
        with open(inverted_index_path, 'r', encoding='utf-8') as f:
            inverted_index = json.load(f)

        # Load catalog (just to count books)
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        total_books = len(catalog)

        num_words = len(inverted_index)
        print(f"Nb of words in inverted index: {num_words}, total books: {total_books}")

        next_progress_words = progress_interval
        candidate_pairs = defaultdict(int)
        book_words = defaultdict(set)

        print("Building graph using inverted index...")

        # --- STEP 1: Count intersections for candidate pairs ---
        for idx, (word, book_list) in enumerate(inverted_index.items(), start=1):

            # Skip overly common words
            if len(book_list) / total_books > self.max_frac:
                continue

            books = []
            for entry in book_list:
                book_id = int(entry['book_id'])  # ensure int
                books.append(book_id)
                book_words[book_id].add(word)

            if len(books) < 2:
                continue

            # manual pair generation
            for i in range(len(books)):
                a = books[i]
                for j in range(i + 1, len(books)):
                    b = books[j]
                    if a > b:
                        a, b = b, a
                    candidate_pairs[(a, b)] += 1

            # progress print
            if idx / num_words >= next_progress_words:
                pct = next_progress_words * 100
                print(f"  Progress: {pct:.1f}% ({idx}/{num_words} words processed)")
                next_progress_words += progress_interval

        total_pairs = len(candidate_pairs)
        self.progress['total_pairs'] = total_pairs
        print(f"Candidate book pairs after filtering: {total_pairs}")

        # --- STEP 2: Compute Jaccard similarity ---
        next_progress_pairs = progress_interval
        for idx, ((a, b), intersection) in enumerate(candidate_pairs.items(), start=1):
            set_a = book_words[a]
            set_b = book_words[b]
            union_size = len(set_a | set_b)
            sim = intersection / union_size if union_size else 0.0

            if sim >= self.threshold:
                self.graph[a].append((b, sim))
                self.graph[b].append((a, sim))

            self.progress['processed_pairs'] = idx

            if idx / total_pairs >= next_progress_pairs:
                pct = next_progress_pairs * 100
                print(f"  Similarity progress: {pct:.1f}% ({idx}/{total_pairs} pairs processed)")
                next_progress_pairs += progress_interval

        # finalize
        total_edges = sum(len(v) for v in self.graph.values()) // 2
        print(f"✓ Graph built: {len(book_words)} nodes, {total_edges} edges")

        self.book_words = book_words
        self.save_graph()

        self.progress['status'] = 'completed'
        self.progress['is_building'] = False
        self.progress['end_time'] = datetime.now().isoformat()

    # ---------------------------------------------------------
    # NEIGHBORS
    # ---------------------------------------------------------

    def get_neighbors(self, book_id) -> List[Tuple[int, float]]:
        """Return neighbors for a book_id (int)."""
        try:
            book_id = int(book_id)
        except:
            return []
        return self.graph.get(book_id, [])

    # ---------------------------------------------------------
    # PAGE RANK (NUMPY)
    # ---------------------------------------------------------

    def calculate_pagerank_numpy(self, damping=0.85, max_iterations=100, tol=1e-6):
        self.progress['is_ranking'] = True

        nodes = list(self.book_words.keys())
        num_books = len(nodes)

        if num_books == 0:
            self.pagerank_scores = {}
            return

        node_to_idx = {node: i for i, node in enumerate(nodes)}
        idx_to_node = nodes

        A = np.zeros((num_books, num_books), dtype=np.float64)

        for a in nodes:
            i = node_to_idx[a]
            for b, weight in self.graph.get(a, []):
                j = node_to_idx[b]
                A[i, j] = weight

        # normalize rows
        row_sums = A.sum(axis=1)
        row_sums[row_sums == 0] = 1
        M = A / row_sums[:, None]

        pr = np.full(num_books, 1.0 / num_books)
        teleport = (1 - damping) / num_books

        print("Starting NUMPY PageRank...")
        print(f"Nodes = {num_books}, Matrix = {num_books}x{num_books}")

        for it in range(max_iterations):
            old_pr = pr.copy()
            pr = teleport + damping * M.T.dot(old_pr)

            delta = np.abs(pr - old_pr).max()
            print(f"  Iter {it + 1}: max_change = {delta:.2e}")

            if delta < tol:
                print(f"✓ Converged after {it + 1} iterations")
                break

        self.pagerank_scores = {idx_to_node[i]: float(pr[i]) for i in range(num_books)}
        self.save_pagerank()
        self.progress['is_ranking'] = False

        print("✓ NUMPY PageRank calculated")

    # ---------------------------------------------------------
    # SAVE / LOAD PAGERANK
    # ---------------------------------------------------------

    def save_pagerank(self):
        with open(self.pagerank_score_save_location, 'w', encoding='utf-8') as f:
            json.dump(self.pagerank_scores, f, indent=2)
        print(f"✓ PageRank saved to {self.pagerank_score_save_location}")

    def load_pagerank(self):
        path = Path(self.pagerank_score_save_location)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # convert keys back to int
            self.pagerank_scores = {int(k): float(v) for k, v in data.items()}
            print(f" PageRank loaded from {self.pagerank_score_save_location}")
            return True
        print(" PageRank not found")
        return False

    # ---------------------------------------------------------
    # SAVE / LOAD GRAPH
    # ---------------------------------------------------------

    def save_graph(self):
        data = {
            'graph': {book_id: neighbors for book_id, neighbors in self.graph.items()},
            'book_words': {book_id: list(words) for book_id, words in self.book_words.items()},
            'threshold': self.threshold,
            'max_frac': self.max_frac
        }
        with open(self.graph_save_location, 'w') as f:
            json.dump(data, f)
        print(f"✓ Graph saved to {self.graph_save_location}")

    def load_graph(self):
        path = Path(self.graph_save_location)
        if not path.exists():
            print("Graph file not found")
            return False

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Restore graph (keys back to int)
            self.graph = defaultdict(
                list,
                {int(k): [(int(n), float(w)) for n, w in v] for k, v in data["graph"].items()}
            )

            # Restore book_words
            self.book_words = {int(k): set(v) for k, v in data["book_words"].items()}

            self.threshold = float(data["threshold"])
            self.max_frac = float(data["max_frac"])

            print(f"✓ Graph loaded from {self.graph_save_location}")
            return True

        except Exception as e:
            print(f"Error loading graph: {e}")
            return False
