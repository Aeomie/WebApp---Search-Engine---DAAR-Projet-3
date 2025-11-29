import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import lru_cache
import time
import numpy as np
from itertools import combinations
class JaccardGraph:
    def __init__(self, threshold=0.1, max_frac=0.2):
        self.threshold = threshold
        self.graph: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.book_words: Dict[str, Set[str]] = {}
        self.inverted_index: Dict[str, List[Tuple[str, float]]] = {}
        self.pagerank_scores: Dict[str, float] = {}
        self.max_frac = max_frac
        self.progress = {
            "total_pairs": 0,
            "processed_pairs": 0
        }

    def build_graph_from_inverted_index(self, inverted_index_path: str, catalog_path: str, progress_interval=0.05):
        """
        Fast graph building using inverted index directly.
        Only compare books that share at least one word.
        Skips words appearing in more than max_frac of books.
        Prints progress based on number of words processed and candidate pairs.
        """
        # Load inverted index
        with open(inverted_index_path, 'r', encoding='utf-8') as f:
            inverted_index = json.load(f)

        # Load catalog to get total number of books
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        total_books = len(catalog)

        num_words = len(inverted_index)
        print(f"Nb of words in inverted index: {num_words}, total books: {total_books}")

        next_progress_words = progress_interval
        candidate_pairs = defaultdict(int)  # (book_a, book_b) -> intersection count
        book_words = defaultdict(set)  # Build book-word sets on the fly

        print("Building graph using inverted index...")

        # Step 1: count intersections for candidate pairs and build book_words at the same time
        for idx, (word, book_list) in enumerate(inverted_index.items(), start=1):
            # Skip overly common words
            if len(book_list) / total_books > self.max_frac:
                continue

            # Build list of book IDs for this word and update book_words
            books = []
            for entry in book_list:
                book_id = entry['book_id']
                books.append(book_id)
                book_words[book_id].add(word)

            if len(books) < 2:
                continue

            # Manual pair generation to avoid combinations overhead
            for i in range(len(books)):
                a = books[i]
                for j in range(i + 1, len(books)):
                    b = books[j]
                    if a > b:
                        a, b = b, a
                    candidate_pairs[(a, b)] += 1

            # Print progress for words
            if idx / num_words >= next_progress_words:
                pct = next_progress_words * 100
                print(f"  Progress: {pct:.1f}% ({idx}/{num_words} words processed)")
                next_progress_words += progress_interval

        total_pairs = len(candidate_pairs)
        print(f"Candidate book pairs after filtering: {total_pairs}")

        # Step 2: compute Jaccard similarity and build the graph with progress
        next_progress_pairs = progress_interval
        for idx, ((a, b), intersection) in enumerate(candidate_pairs.items(), start=1):
            set_a = book_words[a]
            set_b = book_words[b]
            union_size = len(set_a | set_b)
            sim = intersection / union_size if union_size else 0.0

            if sim >= self.threshold:
                self.graph[a].append((b, sim))
                self.graph[b].append((a, sim))

            # Print progress for candidate pairs
            if idx / total_pairs >= next_progress_pairs:
                pct = next_progress_pairs * 100
                print(f"  Similarity progress: {pct:.1f}% ({idx}/{total_pairs} pairs processed)")
                next_progress_pairs += progress_interval

        total_edges = sum(len(v) for v in self.graph.values()) // 2
        print(f"✓ Graph built: {len(book_words)} nodes, {total_edges} edges")
        self.book_words = book_words

    def get_neighbors(self, book_id: str) -> List[Tuple[str, float]]:
        return self.graph.get(book_id, [])

    @staticmethod
    def _compute_node_rank(args):
        node, prob, damping, num_books, graph = args
        rank = (1 - damping) / num_books
        for neighbor, weight in graph.get(node, []):
            neighbor_degree = len(graph.get(neighbor, []))
            if neighbor_degree > 0:
                rank += damping * (prob[neighbor] / neighbor_degree) * weight
        return node, rank


    def calculate_pagerank_numpy(self, damping=0.85, max_iterations=100, tol=1e-6):
        """Fast PageRank using NumPy vectorization (much faster than multiprocessing)"""
        nodes = list(self.book_words.keys())
        num_books = len(nodes)
        if num_books == 0:
            self.pagerank_scores = {}
            return

        # Map node IDs to row/column indices
        node_to_idx = {node: i for i, node in enumerate(nodes)}
        idx_to_node = nodes

        # --- Build a weighted adjacency matrix A (dense) ---

        A = np.zeros((num_books, num_books), dtype=np.float64)

        for a in nodes:
            i = node_to_idx[a]
            neighbors = self.graph.get(a, [])
            for b, weight in neighbors:
                j = node_to_idx[b]
                A[i, j] = weight

        # --- Normalize rows by degree (outgoing sum) ---

        row_sums = A.sum(axis=1)
        row_sums[row_sums == 0] = 1  # avoid division by zero
        M = A / row_sums[:, None]  # stochastic matrix

        # --- PageRank iterative computation ---
        pr = np.full(num_books, 1.0 / num_books, dtype=np.float64)
        teleport = (1 - damping) / num_books

        print("Starting NUMPY PageRank...")
        print(f"Nodes = {num_books}, Matrix = {num_books}x{num_books}")

        for it in range(max_iterations):
            old_pr = pr.copy()

            pr = teleport + damping * M.T.dot(old_pr)

            # compute convergence
            delta = np.abs(pr - old_pr).max()

            print(f"  Iter {it + 1:3d}: max_change = {delta:.2e}")

            if delta < tol:
                print(f"✓ Converged after {it + 1} iterations")
                break

        # map back to node IDs
        self.pagerank_scores = {
            idx_to_node[i]: float(pr[i]) for i in range(num_books)
        }

        print("✓ NUMPY PageRank calculated")
    def save_pagerank(self, filepath: str):
        """Save pagerank_scores to a JSON file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.pagerank_scores, f, ensure_ascii=False, indent=2)
        print(f"✓ PageRank saved to {filepath}")

    def load_pagerank(self, filepath: str):
        """Load pagerank_scores from a JSON file"""
        path = Path(filepath)
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                self.pagerank_scores = json.load(f)
            print(f"✓ PageRank loaded from {filepath}")
        else:
            print(f"⚠️ File {filepath} not found. You need to compute PageRank first.")
