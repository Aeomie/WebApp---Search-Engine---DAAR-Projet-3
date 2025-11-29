import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


class JaccardGraph:
    def __init__(self, threshold=0.1, num_processes=4):
        self.threshold = threshold
        self.graph: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.book_words: Dict[str, Set[str]] = {}
        self.inverted_index: Dict[str, List[Tuple[str, float]]] = {}
        self.pagerank_scores: Dict[str, float] = {}
        self.progress = {
            "total_pairs": 0,
            "processed_pairs": 0
        }
        self.num_processes = num_processes

    def build_book_words_from_index(self, filepath: str):
        """
        Build book words from inverted index
        Transform from: word -> list of (book_id, frequency)
        to book_id -> set of words
        """
        with open(filepath, 'r') as f:
            inverted_index = json.load(f)

        for word, book_list in inverted_index.items():
            for entry in book_list:
                book_id = entry['book_id']
                if book_id not in self.book_words:
                    self.book_words[book_id] = set()
                self.book_words[book_id].add(word)

    @staticmethod
    def _compute_similarity_chunk(chunk):
        """Compute Jaccard similarities for a list of book pairs"""
        results = []
        for book_a, book_b, book_words in chunk:
            set_a = book_words[book_a]
            set_b = book_words[book_b]
            union = set_a | set_b
            if not union:
                sim = 0.0
            else:
                sim = len(set_a & set_b) / len(union)
            results.append((book_a, book_b, sim))
        return results

    def build_graph_parallel(self, batch_size=10000):
        """Build similarity graph using batching and multiprocessing"""
        books = list(self.book_words.keys())
        total_pairs = len(books) * (len(books) - 1) // 2
        self.progress["total_pairs"] = total_pairs
        self.progress["processed_pairs"] = 0

        # Generate all book pairs in batches
        pairs = [(books[i], books[j], self.book_words) for i in range(len(books)) for j in range(i+1, len(books))]

        # Split into chunks for processes
        chunks = [pairs[i:i + batch_size] for i in range(0, len(pairs), batch_size)]

        with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
            futures = [executor.submit(self._compute_similarity_chunk, chunk) for chunk in chunks]

            for future in as_completed(futures):
                results = future.result()
                for book_a, book_b, sim in results:
                    if sim >= self.threshold:
                        self.graph[book_a].append((book_b, sim))
                        self.graph[book_b].append((book_a, sim))

                # Update progress
                self.progress["processed_pairs"] += len(results)
                if self.progress["processed_pairs"] % 10000 == 0:
                    progress_pct = (self.progress["processed_pairs"] / total_pairs) * 100
                    print(f"  Progress: {progress_pct:.1f}% ({self.progress['processed_pairs']}/{total_pairs} pairs)")

        total_edges = sum(len(neighbors) for neighbors in self.graph.values()) // 2
        print(f"✓ Graph built: {len(self.book_words)} nodes, {total_edges} edges")

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

    def calculate_pagerank_parallel(self, damping=0.85, max_iterations=100, tol=1.0e-6):
        """Calculate PageRank using multiprocessing per node"""
        nodes = list(self.book_words.keys())
        num_books = len(nodes)
        if num_books == 0:
            self.pagerank_scores = {}
            return

        prob = {node: 1.0 / num_books for node in nodes}

        for iteration in range(max_iterations):
            args_list = [(node, prob, damping, num_books, self.graph) for node in nodes]

            with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
                results = executor.map(self._compute_node_rank, args_list)

            new_prob = dict(results)
            max_change = max(abs(new_prob[node] - prob[node]) for node in nodes)
            prob = new_prob

            if max_change < tol:
                print(f"  Converged after {iteration + 1} iterations")
                break

        self.pagerank_scores = prob
        print("✓ PageRank calculated")
