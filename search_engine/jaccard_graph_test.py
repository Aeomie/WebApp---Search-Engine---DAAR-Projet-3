from JaccardGraph import JaccardGraph

if __name__ == "__main__":
    # Create graph object
    jaccard_graph = JaccardGraph(threshold=0.1, num_processes=4)

    # Load book-word mapping
    jaccard_graph.build_book_words_from_index("../books_data//index_TableTC.json")

    # Build similarity graph in parallel
    jaccard_graph.build_graph_parallel()

    # Compute PageRank in parallel
    jaccard_graph.calculate_pagerank_parallel()
