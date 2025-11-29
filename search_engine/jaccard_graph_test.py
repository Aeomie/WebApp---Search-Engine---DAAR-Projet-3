from JaccardGraph import JaccardGraph
jaccard_graph = JaccardGraph(threshold=0.2)
jaccard_graph.build_book_words_from_index('../books_data/index_TableTC.json')
jaccard_graph.build_graph()

for book_id, edges in jaccard_graph.graph.items():
    print(f"Book ID: {book_id}")
    for neighbor_id, similarity in edges:
        print(f"  Neighbor ID: {neighbor_id}, Jaccard Similarity: {similarity:.4f}")