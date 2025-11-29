import json
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class JaccardGraph:
    def __init__(self, threshold=0.1):
        self.threshold = threshold
        self.graph: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.book_words: Dict[str, Set[str]] = {}
        self.inverted_index: Dict[str, List[Tuple[str, float]]] = {}
        self.pagerank_scores: Dict[str, float] = {}

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

    def jaccard_similarity(self, set1: Set[str], set2: Set[str]) -> float:
        """
        Calculate Jaccard similarity between two sets:
        Jaccard(A, B) = |A ∩ B| / |A ∪ B|
        """
        if not set1 and not set2:
            return 0.0
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union > 0 else 0.0

    def build_graph(self):
        """
        Build a similarity graph where edges exist if Jaccard similarity >= threshold
        """
        books = list(self.book_words.keys())
        total_pairs = len(books) * (len(books) - 1) // 2
        processed_pairs = 0

        for i in range(len(books)):
            for j in range(i + 1, len(books)):
                book_a = books[i]
                book_b = books[j]

                similarity = self.jaccard_similarity(
                    self.book_words[book_a], self.book_words[book_b]
                )
                if similarity >= self.threshold:
                    self.graph[book_a].append((book_b, similarity))
                    self.graph[book_b].append((book_a, similarity))

                processed_pairs += 1
                if processed_pairs % 10000 == 0:
                    progress = (processed_pairs / total_pairs) * 100
                    print(f"  Progress: {progress:.1f}% ({processed_pairs}/{total_pairs} pairs)")

        total_edges = sum(len(neighbors) for neighbors in self.graph.values()) // 2
        print(f"✓ Graph built: {len(self.book_words)} nodes, {total_edges} edges")

    def get_neighbors(self, book_id: str) -> List[Tuple[str, float]]:
        return self.graph.get(book_id, [])

    def calculate_pagerank(self, damping=0.85, max_iterations=100, tol=1.0e-6):
        """
        Calculate PageRank centrality
        PR(A) = (1-d) / N + d * sum(PR(B) / L(B)) for neighbors B
        """
        nodes = list(self.book_words.keys())
        num_books = len(nodes)
        if num_books == 0:
            self.pagerank_scores = {}
            return

        # Initialize probability for each node
        prob = {node: 1.0 / num_books for node in nodes}

        for iteration in range(max_iterations):
            new_prob = {}
            max_change = 0

            for node in nodes:
                rank = (1 - damping) / num_books  # random jump factor

                for neighbor, weight in self.get_neighbors(node):
                    neighbor_degree = len(self.get_neighbors(neighbor))
                    if neighbor_degree > 0:
                        # weighted PageRank (optional, can remove weight if needed)
                        rank += damping * (prob[neighbor] / neighbor_degree) * weight

                new_prob[node] = rank
                max_change = max(max_change, abs(new_prob[node] - prob[node]))

            prob = new_prob

            if max_change < tol:
                print(f"  Converged after {iteration + 1} iterations")
                break

        self.pagerank_scores = prob
        print("✓ PageRank calculated")
